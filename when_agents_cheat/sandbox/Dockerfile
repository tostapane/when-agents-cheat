# Sandbox for model-written code. Used by every benchmark, model and setting.
FROM aisiuk/inspect-tool-support@sha256:8571d6fb1d3439f8ef368784c7e9692c80845bb52d660b9943bf979b96561d06

# HumanEval+ tests need numpy. Same version as uv.lock.
RUN pip install --no-cache-dir numpy==2.5.4

WORKDIR /workspace
