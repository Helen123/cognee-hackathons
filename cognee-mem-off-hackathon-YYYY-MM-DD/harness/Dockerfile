# Mem Off runner image: Python 3.14 for xitkit, Node for Claude Code, uv, the harness.
FROM python:3.14-slim
ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates nodejs npm && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && ln -s /root/.local/bin/uv /usr/local/bin/uv
# Pin Claude Code with the frozen benchmark (see action-run.json of the reference run).
ARG CLAUDE_CODE_VERSION=latest
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}
WORKDIR /benchmark
COPY harness /benchmark/harness
COPY challenge /benchmark/challenge
RUN cd /benchmark/harness && uv venv -p 3.14 .venv && uv pip install -p .venv/bin/python -e ".[dev]"
ENV PATH="/benchmark/harness/.venv/bin:${PATH}" MEMOFF_ISSUES_DIR=/benchmark/challenge/issues
# The cognee plugin (for the cognee-report skill) is installed at container start, after
# ANTHROPIC_API_KEY / claude login is available: `claude plugin marketplace add … && claude plugin install …`.
ENTRYPOINT ["memoff"]
