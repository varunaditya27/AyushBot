# =============================================================================
# AyushBot Backend — LLM Model Loader & Memory Manager
# =============================================================================
#
# PURPOSE:
#   Handles loading, initialization, and lifecycle management of the quantized
#   on-device LLM. The model is loaded ONCE at gateway startup and kept in
#   memory for the lifetime of the process.
#
# MODEL OPTIONS (configured in config.yaml):
#   Primary: Microsoft Phi-3 Mini (3.8B params), 4-bit GPTQ quantized
#     - ~2 GB disk, ~2.5 GB RAM (with KV cache)
#     - Quality: Near-GPT-3.5 on clinical reasoning benchmarks
#     - Runs via llama.cpp (GGUF format) or CTranslate2 on RPi 4 CPU
#
#   Fallback: Google Gemma-3 1B, 4-bit quantized
#     - ~0.6 GB disk, ~1 GB RAM
#     - Lower quality but significantly faster; used if RPi 4 memory is tight
#
# LOADING STRATEGY:
#   1. Read model configuration from config.yaml (model_path, quantization,
#      context_length, max_tokens, temperature)
#   2. Load the GGUF model file using llama-cpp-python bindings:
#      - n_ctx = 2048 (context window; enough for 5 chunks + prompt + response)
#      - n_threads = 2 (leave 2 cores free for other agents)
#      - n_gpu_layers = 0 (RPi 4 has no GPU; pure CPU inference)
#   3. Warm up with a dummy prompt to trigger JIT compilation and memory
#      allocation. Log the warm-up time.
#   4. Return the model handle as a singleton accessible by inference.py
#
# MEMORY MANAGEMENT:
#   On RPi 4 (4 GB RAM), memory budget is tight:
#     - OS + system: ~500 MB
#     - FAISS index + BM25: ~100 MB
#     - Bi-encoder + Cross-encoder: ~200 MB
#     - LLM: ~2 GB (Phi-3) or ~1 GB (Gemma-3)
#     - Remaining: headroom for Python runtime + FL training
#   The loader monitors available memory before loading and falls back to
#   the smaller model if insufficient RAM is detected.
#
# MODEL SWAPPING:
#   If a new model version is deployed (e.g., updated quantization), the
#   loader can unload the current model and load the new one without
#   restarting the gateway process. This is triggered via an admin API
#   endpoint or a config file change watcher.
#
# INPUTS:
#   - config.yaml "llm" section: model_path, quantization, context_length, etc.
#
# OUTPUTS:
#   - Singleton LLM model handle (llama_cpp.Llama or CTranslate2 model object)
#   - Model metadata: name, params, quantization, context_length, load_time_ms
# =============================================================================
