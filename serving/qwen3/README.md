# Serving Qwen3-14B

Ollama 0.40.16 on Windows, model `qwen3:14b` (Q4_K_M, digest `bdbd181c33f2`).

1. Install Ollama and run `ollama pull qwen3:14b`.
2. Set context length to 32768 (Ollama Settings, or `OLLAMA_CONTEXT_LENGTH=32768`)
   and `OLLAMA_NUM_PARALLEL=1`, then restart Ollama. A shorter context cuts
   agent conversations without an error.
3. Check with `ollama ps` after a run: CONTEXT should be 32768, PROCESSOR 100% GPU.

Thinking is on by default; the `*_nothink` configs turn it off.
Pilot speed (thinking on): about 48 s per HumanEval+ task, 2.2 hours for all 164.
