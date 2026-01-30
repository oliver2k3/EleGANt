import os
import torch


def setup_cpu_optimization(num_threads: int = 6, num_interop_threads: int = 2):
    os.environ.setdefault("OMP_NUM_THREADS", str(num_threads))
    os.environ.setdefault("MKL_NUM_THREADS", str(num_threads))
    os.environ.setdefault("KMP_BLOCKTIME", "1")
    os.environ.setdefault("KMP_AFFINITY", "granularity=fine,compact,1,0")
    
    torch.set_num_threads(num_threads)
    torch.set_num_interop_threads(num_interop_threads)
    
    return {
        "num_threads": torch.get_num_threads(),
        "num_interop_threads": torch.get_num_interop_threads(),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS")
    }


def get_optimization_status():
    return {
        "num_threads": torch.get_num_threads(),
        "num_interop_threads": torch.get_num_interop_threads(),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS", "not set"),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS", "not set"),
        "kmp_blocktime": os.environ.get("KMP_BLOCKTIME", "not set"),
        "kmp_affinity": os.environ.get("KMP_AFFINITY", "not set")
    }
