# Cluster runbook for the ML slice (Arsenii)

Machines: `dice-fuji1` and `dice-fuji3` (4x RTX A6000 48 GB each). Storage: `/mnt/raid0hdd1/users/arsenii/`. Everything below runs **inside WSL** on the laptop, never in PowerShell.

**Status 18 Oct:** every job so far, including the matcher fine-tune, ran on the laptop GPU in minutes. The cluster is only for the optional bulk LLM labelling (M2 in-house exposure check). Nothing in the demo depends on it.

## 0. Rules

- **The cluster makes no external API calls.** All data is fetched and checked on the laptop, then copied up. Only model downloads might need the internet there, and even those can be copied up from the laptop.
- Read `~/RULE.md` on the cluster before the first job.
- One GPU per job (`CUDA_VISIBLE_DEVICES`), in `nohup` or `tmux`. Kill only your own PIDs, never `pkill python`.
- Nothing in the demo depends on the cluster. Every artefact is copied back to the laptop the same night.

## 1. What runs where

| Job | Where | Why |
| --- | --- | --- |
| ASHE, crosswalks, ILO, CPIH, backtest, demand, resilience, hedge baseline | Laptop CPU | Small tables; already working |
| Matcher baselines (keyword, off-the-shelf embeddings) | Laptop GPU (`torch-cuda` env) | BGE-base is 110M parameters, minutes on the 5070 Ti |
| Matcher fine-tune | Laptop GPU first; fuji1 GPU 0 only if it's too slow | Only if the baseline result says it's worth trying |
| In-house exposure labelling of all ESCO tasks with a local LLM (vLLM) | fuji1 GPUs 1-3 | Tens of thousands of tasks; avoids the ELM budget |

## 2. Connection (one-time)

The WSL `~/.ssh/config` already routes `dice-fuji1` and `dice-fuji3` through the student gateway, so `ssh`, `scp` and `rsync` to those names work with no `-J`. Add connection sharing so later calls are instant:

```
cat >> ~/.ssh/config <<'EOF'

Host dice-*
    ControlMaster auto
    ControlPath ~/.ssh/cm-%C
    ControlPersist 4h
    ServerAliveInterval 30
    ServerAliveCountMax 4
EOF
```

On "Permission denied (publickey...)", load the key with `ssh-add ~/.ssh/gpu_cluster`. If ssh hangs after the laptop slept, run `ssh -O exit dice-fuji1`.

## 3. First checks on the cluster

```
ssh dice-fuji1 'cat ~/RULE.md; df -h /mnt/raid0hdd1 ~; nvidia-smi --query-gpu=index,memory.used --format=csv'
ssh dice-fuji1 'mkdir -p /mnt/raid0hdd1/users/arsenii/pathfinder/{code,data,models,artefacts,logs}'
ssh dice-fuji1 'python3 --version; curl -sI https://huggingface.co | head -1'
```

## 4. Environment (on fuji1)

```
cd /mnt/raid0hdd1/users/arsenii/pathfinder
python3 -m venv .venv && . .venv/bin/activate && pip install -U pip
pip install torch --index-url https://download.pytorch.org/whl/cu128
pip install sentence-transformers pandas pyarrow scipy scikit-learn
export HF_HOME=/mnt/raid0hdd1/users/arsenii/pathfinder/models
python -c "import torch; print(torch.cuda.device_count(), torch.cuda.get_device_name(0))"
```

If huggingface.co is blocked, download the model on the laptop and copy the cache up (step 5).

## 5. Moving files (from WSL)

Set `REPO=/mnt/c/Users/<you>/code/KATYATA` (the repo as seen from WSL) first. A trailing `/` on the source means "copy the contents". Add `-n` first for a dry run, and never use `--delete` towards the cluster.

```
rsync -avhP --exclude .git --exclude __pycache__ $REPO/packages/ml/ dice-fuji1:/mnt/raid0hdd1/users/arsenii/pathfinder/code/
rsync -avhP $REPO/data/processed/ dice-fuji1:/mnt/raid0hdd1/users/arsenii/pathfinder/data/processed/
rsync -avhP dice-fuji1:/mnt/raid0hdd1/users/arsenii/pathfinder/artefacts/ $REPO/snapshots/ml/
rsync -avhP --exclude '*.safetensors' --exclude '*.pt' dice-fuji1:/mnt/raid0hdd1/users/arsenii/pathfinder/models/ $REPO/data/models/
```

Only `artefacts/` (JSON) comes back into the repo. Model weights stay out of git.

## 6. Running a job (on fuji1)

```
cd /mnt/raid0hdd1/users/arsenii/pathfinder && . .venv/bin/activate
CUDA_VISIBLE_DEVICES=0 nohup python code/scripts/<script>.py <args> > logs/<name>_$(date +%F_%H%M).log 2>&1 & echo $!
tail -f logs/<name>_*.log          # watch it
ps -p <PID>                        # still running?
kill <PID>                         # stop your own job only
```

For a local LLM (exposure labelling), run `CUDA_VISIBLE_DEVICES=1,2,3 vllm serve <model> --tensor-parallel-size 3` in its own session. Check free disk first, and stop it when the batch is done.

## 7. Before logging off

- Copy every artefact back (step 5) and rerun the contract tests on the laptop.
- Note in the branch context file which artefacts exist and which script and commit produced them.
- Leave no idle server holding GPUs.
