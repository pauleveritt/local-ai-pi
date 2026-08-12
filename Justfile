# Local ds4 tooling from this project.
#
# `ds4-0731` starts the ds4 coding agent for DeepSeek V4 Flash 0731, working
# in THIS project's directory. The binary and models live in the ds4
# main-tooling worktree; --chdir moves the agent here so it reads/writes
# files in this project. The scoped HOME isolates agent history and anything
# home-relative in the same place as the ds4-0731 server, so the two never
# collide and never share KV state with other models.
#
# DSpark (--dspark --mtp) only accelerates greedy (temperature=0) requests;
# the agent defaults to sampled decoding, so DSpark is idle unless --temp 0
# is added.
ds4_workspace := "/Users/pauleveritt/projects/ds4/.claude/worktrees/main-tooling"

ds4-0731 ctx="80000":
    cd {{ds4_workspace}} \
    && HOME={{env_var("HOME")}}/.local/state/ds4-home/ds4-flash-0731 \
        {{ds4_workspace}}/ds4-agent-0731.sh \
        -m {{ds4_workspace}}/gguf/DeepSeek-V4-Flash-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-chat-v2-imatrix-0731.gguf \
        --dspark --mtp {{ds4_workspace}}/gguf/DeepSeek-V4-Flash-DSpark-support.gguf \
        -c {{ctx}} \
        --chdir {{env_var("PWD")}}

# Start the matching OpenAI-compatible ds4-server. Port 8001 is already used
# by the local oMLX server, so this defaults to 8002. The server-only KV cache
# shares the model-scoped HOME with the agent while remaining isolated from
# other ds4 model instances.
ds4-0731-server ctx="80000" port="8002":
    mkdir -p {{env_var("HOME")}}/.local/state/ds4-home/ds4-flash-0731/kv
    cd {{ds4_workspace}} \
    && HOME={{env_var("HOME")}}/.local/state/ds4-home/ds4-flash-0731 \
        {{ds4_workspace}}/ds4-server \
        -m {{ds4_workspace}}/gguf/DeepSeek-V4-Flash-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-chat-v2-imatrix-0731.gguf \
        --dspark --mtp {{ds4_workspace}}/gguf/DeepSeek-V4-Flash-DSpark-support.gguf \
        -c {{ctx}} \
        --port {{port}} \
        --kv-disk-dir {{env_var("HOME")}}/.local/state/ds4-home/ds4-flash-0731/kv \
        --kv-disk-space-mb 16384
