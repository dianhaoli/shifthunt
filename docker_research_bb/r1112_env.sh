# Source before launching research-1112 (black-box study) rollouts, from tasks/shifthunt of the private harness.
# Same settings as the main study's scripts/r1103_env.sh except the image suffix and the pause file.
# This file holds no secret: the keys are read from the box's .env. scripts/blackbox_sync_private.sh installs
# it as tasks/shifthunt/scripts/r1112_env.sh.
source /home/ec2-user/onsite/.env
export RL_TASK_IMAGE_SUFFIX=-r1112
export OPENAI_API_KEY="$OPENAI_KEY" OPENAI_API_IP=172.66.0.243 CODEX_EFFORT=max
export OPENAI_PRICES=1.0,0.05,1.25,5.0   # gpt-6.1-terra standard (input, cache read, cache write 30 min, output)
export LAUNCH_PAUSE_FILE=results/rollouts/r1112_pause
PY=/home/ec2-user/onsite/grader-wt/.venv/bin/python
