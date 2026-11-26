#!/usr/bin/env bash
set -euo pipefail
umask 077

usage() {
  printf 'Usage: %s ACTIVATION_RECEIPT | --stage-only\n' "${0##*/}"
}

if [[ "$#" != 1 ]]; then
  usage >&2
  exit 2
fi
if [[ "$1" == --help ]]; then
  usage
  exit 0
fi

stage_only=false
if [[ "$1" == --stage-only ]]; then
  stage_only=true
else
  : "${SLURM_JOB_ID:?Run this inside the four-GPU Slurm allocation}"
  [[ "$(uname -s)" == Linux && "${SLURM_JOB_NUM_NODES:-${SLURM_NNODES:-1}}" == 1 ]]
  [[ "$1" == /* && ! -s "$1" && ! -L "$1" && -d "$(dirname "$1")" ]] || {
    printf 'Use an absolute path to an empty or new activation receipt.\n' >&2
    exit 2
  }
  receipt="$1"
fi

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
checkouts="${EVIDENCESTORE_LIFECYCLE_CHECKOUTS:-$repo/third_party/checkouts}"
if [[ -z "${EVIDENCESTORE_LIFECYCLE_CHECKOUTS:-}" && ! -d "$checkouts" ]]; then
  checkouts="$repo/../evidence_store_2/third_party/checkouts"
fi
node_root="/tmp/$(id -un)"
mkdir -p -- "$node_root"
[[ -d "$node_root" && -O "$node_root" && ! -L "$node_root" ]]
runtime="$(mktemp -d "$node_root/es-kv-lifecycle-${SLURM_JOB_ID:-stage}.XXXXXX")"
runtime="$(cd -- "$runtime" && pwd -P)"
check="$runtime/check"
mkdir -p -- "$check"
export VLLM_LIFECYCLE_SOURCE="$runtime/build/vllm"
export LMCACHE_LIFECYCLE_SOURCE="$runtime/build/lmcache"

(
  printf 'Runtime scratch %s\n' "$runtime"
  df -h "$runtime"

  # The checkout helper verifies detached, clean, remote-free parents with
  # their own Git objects. The scratch fetch is restricted to its file URI.
  python3 -B - "$repo" "$checkouts" "$runtime" <<'PY'
from hashlib import sha256
import json
from pathlib import Path
import sys

repo, checkouts, runtime = (Path(arg).resolve() for arg in sys.argv[1:])
sys.path.insert(0, str(repo / "scripts"))
from checkout_sources import fetch_local_commit, git, source_pins, verify

pins = source_pins()
sources = {}
for name in ("vllm", "lmcache"):
    source = checkouts / name
    commit = pins[name]
    verify(source, commit)
    destination = runtime / "build" / name
    destination.mkdir(parents=True)
    fetch_local_commit(destination, source, commit)
    git(destination, "switch", "--quiet", "--detach", "FETCH_HEAD")
    verify(destination, commit)
    patch = repo / "third_party" / "lifecycle" / f"{name}.patch"
    git(destination, "apply", "--check", patch)
    git(destination, "apply", patch)
    sources[name] = {"commit": commit, "local_source": str(source),
                     "scratch_source": str(destination),
                     "patch_sha256": sha256(patch.read_bytes()).hexdigest()}
    print(f"Staged {name} at {commit} from {source}", flush=True)

(runtime / "check" / "sources.json").write_text(
    json.dumps(sources, indent=2) + "\n", encoding="utf-8"
)
PY
  if "$stage_only"; then
    printf 'Verified local source staging at %s\n' "$check/sources.json"
    exit 0
  fi

  if ! command -v uv >/dev/null && [[ -x "$node_root/uv-bin/uv" ]]; then
    export PATH="$node_root/uv-bin:$PATH"
  fi
  command -v uv nvidia-smi
  nvidia-smi --query-gpu=uuid,name,driver_version --format=csv
  if [[ -z "${CC:-}${CXX:-}" ]] && command -v gcc-13 g++-13 >/dev/null; then
    export CC=gcc-13 CXX=g++-13
  fi
  export CC="${CC:-gcc}" CXX="${CXX:-g++}"
  command -v "$CC" "$CXX"
  compiler="$(command -v "$CXX")"
  unset PYTHONHOME PYTHONOPTIMIZE VLLM_USE_V2_MODEL_RUNNER TRANSFORMERS_CACHE
  unset VLLM_USE_PRECOMPILED VLLM_USE_PRECOMPILED_RUST VLLM_PRECOMPILED_WHEEL_LOCATION \
    VLLM_PRECOMPILED_WHEEL_COMMIT VLLM_PRECOMPILED_WHEEL_VARIANT
  export PYTHONNOUSERSITE=1 PYTHONPATH="$repo/scripts"
  export UV_PYTHON_INSTALL_DIR="$runtime/uv-python" UV_PYTHON_CACHE_DIR="$runtime/uv-python-cache"
  export UV_CACHE_DIR="$node_root/uv-cache"
  export HF_HOME="$node_root/huggingface" HF_HUB_CACHE="$node_root/huggingface/hub"
  export TMPDIR="$runtime/tmp" XDG_CACHE_HOME="$runtime/xdg-cache"
  export TRITON_CACHE_DIR="$runtime/triton" CUDA_CACHE_PATH="$runtime/cuda-cache"
  export TORCH_EXTENSIONS_DIR="$runtime/torch-extensions" VLLM_RPC_BASE_PATH="$runtime/rpc"
  export MAX_JOBS="${MAX_JOBS:-4}" TORCH_CUDA_ARCH_LIST="${TORCH_CUDA_ARCH_LIST:-8.6}"
  mkdir -p -- "$UV_CACHE_DIR" "$UV_PYTHON_INSTALL_DIR" "$UV_PYTHON_CACHE_DIR" \
    "$HF_HUB_CACHE" "$TMPDIR" "$XDG_CACHE_HOME" "$VLLM_RPC_BASE_PATH"

  uv --no-config python install --no-bin 3.12.14
  base_python="$(env -u VIRTUAL_ENV -u CONDA_PREFIX uv --no-config --offline python find \
    --managed-python --no-python-downloads 3.12.14)"
  base_python="$(readlink -f -- "$base_python")"
  [[ "$base_python" == "$UV_PYTHON_INSTALL_DIR/"* && -x "$base_python" ]]
  uv --no-config venv --python "$base_python" --no-python-downloads "$runtime/venv"
  python="$runtime/venv/bin/python"
  "$python" -I -c 'import ssl, sys; assert sys.version_info[:3] == (3, 12, 14); print(sys.executable)'

  cuda_home="${CUDA_HOME:-}"
  if [[ -z "$cuda_home" ]] && system_nvcc="$(command -v nvcc)"; then
    cuda_home="$(dirname "$(dirname "$(readlink -f -- "$system_nvcc")")")"
  fi
  cuda_info=""
  if [[ -n "$cuda_home" && -x "$cuda_home/bin/nvcc" ]]; then
    cuda_info="$("$cuda_home/bin/nvcc" --version)" || cuda_info=""
  fi
  if [[ "$cuda_info" != *'release 13.2,'* ]]; then
    uv --no-config pip install --python "$python" 'cuda-toolkit[nvcc,cccl]==13.2.1'
    cuda_home="$("$python" -c 'import sysconfig; print(sysconfig.get_path("purelib") + "/nvidia/cu13")')"
    if [[ ! -e "$cuda_home/lib/libcudart.so" ]]; then
      test -f "$cuda_home/lib/libcudart.so.13"
      ln -s libcudart.so.13 "$cuda_home/lib/libcudart.so"
    fi
  fi
  export CUDA_HOME="$cuda_home" CUDA_INC_PATH="$cuda_home/include/cccl"
  export PATH="$CUDA_HOME/bin:$PATH"
  cuda_info="$("$CUDA_HOME/bin/nvcc" --version)"
  [[ "$cuda_info" == *'release 13.2,'* ]]
  printf 'CUDA toolkit %s\n%s\n' "$CUDA_HOME" "$cuda_info"

  cat > "$TMPDIR/nvcc-probe.cu" <<'CUDA'
#include <cuda_runtime.h>
#include <cub/cub.cuh>

__global__ void probe() {}
int main() { return static_cast<int>(cudaGetLastError()); }
CUDA
  "$CUDA_HOME/bin/nvcc" -arch=sm_86 -ccbin "$compiler" --cudart shared \
    "$TMPDIR/nvcc-probe.cu" -o "$TMPDIR/nvcc-probe"

  vllm_pin="$(git -C "$VLLM_LIFECYCLE_SOURCE" rev-parse HEAD)"
  VLLM_USE_PRECOMPILED=1 VLLM_PRECOMPILED_WHEEL_COMMIT="$vllm_pin" VLLM_PRECOMPILED_WHEEL_VARIANT=cu132 \
    uv --no-config pip install --python "$python" --torch-backend=cu132 --editable "$VLLM_LIFECYCLE_SOURCE"
  "$runtime/venv/bin/vllm" download-kernels
  uv --no-config pip install --python "$python" -r "$LMCACHE_LIFECYCLE_SOURCE/requirements/build.txt"
  BUILD_WITH_CUDA=1 NO_GPU_EXT=0 LMCACHE_CUDA_MAJOR=13 \
    uv --no-config pip install --python "$python" --no-build-isolation --editable "$LMCACHE_LIFECYCLE_SOURCE"
  uv --no-config pip check --python "$python"

  "$python" - "$check/sources.json" <<'PY' | tee "$check/runtime.json"
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys

import torch
import vllm
import vllm._C
import lmcache
import lmcache.cuda_ops
from lmcache.integration.vllm.lmcache_mp_connector import LMCacheMPConnector
from vllm.v1.worker.gpu.lifecycle import emit_kv_writes

if torch.cuda.device_count() != 4 or torch.version.cuda != "13.2":
    raise SystemExit("Expected Torch CUDA 13.2 with exactly four visible GPUs")
for module, name in ((vllm, "VLLM"), (lmcache, "LMCACHE")):
    if not Path(module.__file__).resolve().is_relative_to(os.environ[f"{name}_LIFECYCLE_SOURCE"]):
        raise SystemExit(f"Expected scratch editable module for {name}: {module.__file__}")
print(json.dumps({
    "sources": json.loads(Path(sys.argv[1]).read_text()),
    "versions": {name: version(name) for name in ("vllm", "lmcache", "torch")},
    "torch_cuda": torch.version.cuda,
    "gpu_count": torch.cuda.device_count(),
    "vllm_native": vllm._C.__file__,
    "lmcache_native": lmcache.cuda_ops.__file__,
    "model_write_hook": emit_kv_writes.__module__,
    "connector": LMCacheMPConnector.__module__,
}, indent=2))
PY

  activation="$runtime/activate.sh"
  export EVIDENCESTORE_LIFECYCLE_RUNTIME="$runtime"
  export EVIDENCESTORE_LIFECYCLE_PYTHON="$python"
  {
    printf 'unset PYTHONHOME PYTHONOPTIMIZE TRANSFORMERS_CACHE\n'
    for name in EVIDENCESTORE_LIFECYCLE_RUNTIME EVIDENCESTORE_LIFECYCLE_PYTHON \
      VLLM_LIFECYCLE_SOURCE LMCACHE_LIFECYCLE_SOURCE PYTHONNOUSERSITE PYTHONPATH \
      CUDA_HOME CUDA_INC_PATH HF_HOME HF_HUB_CACHE TMPDIR XDG_CACHE_HOME \
      TRITON_CACHE_DIR CUDA_CACHE_PATH TORCH_EXTENSIONS_DIR VLLM_RPC_BASE_PATH; do
      printf 'export %s=%q\n' "$name" "${!name}"
    done
    printf 'export PATH=%q:"$PATH"\n' "$CUDA_HOME/bin"
    printf 'source %q\n' "$runtime/venv/bin/activate"
  } > "$activation"
  receipt_tmp="$(mktemp "${receipt}.XXXXXX")"
  trap 'rm -f -- "$receipt_tmp"' EXIT
  printf '%s\n' "$activation" > "$receipt_tmp"
  mv -f -- "$receipt_tmp" "$receipt"
  printf 'Verified runtime activation %s\n' "$activation"
) 2>&1 | tee "$check/setup.log"
