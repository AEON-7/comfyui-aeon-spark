# ComfyUI · AEON DGX Spark · Flux 2 + LTX 2.3 + ACE-Step (BF16)


[![☕ Tips](https://img.shields.io/badge/%E2%98%95_Tips-Support_the_work-ff5e5b?style=flat)](https://github.com/AEON-7/AEON-7#-support-the-work)
> Bleeding-edge ComfyUI distribution **purpose-built for the NVIDIA DGX
> Spark (GB10 / Blackwell / sm_121a)**. Ships with Flux 2 Dev, LTX 2.3
> 22B, and ACE-Step v1.5 XL Turbo pre-staged at full BF16 quality plus
> NVFP4 hardware-accelerated alternates and abliterated text-encoder
> paths. CUDA 13.0.2 + PyTorch cu130 + SageAttention v3 compiled for
> sm_121a + NVFP4 (CUTLASS) hardware GEMMs.

```
docker pull ghcr.io/aeon-7/comfyui-aeon-spark:latest          # auto-downloads weights using your HF_TOKEN
docker pull ghcr.io/aeon-7/comfyui-aeon-spark:slim            # no auto-download — pick models via UI
```

---

## 🚀 Fastest path — 4 steps, ~50 minutes

**Run these in order on a DGX Spark host. No prior knowledge needed.**

### Step 1: Get a HuggingFace token (5 min, free)

Open in browser: **https://huggingface.co/settings/tokens**
Click **"New token"** → name it `comfyui-aeon-spark` → scope = **Read** → **Create token** → copy it.
Save it for Step 3. Token starts with `hf_`.

### Step 2: Accept 3 gated model licenses (3 click-throughs, free)

While logged in to HuggingFace, open each link below and click **"Agree and access"**:

1. https://huggingface.co/black-forest-labs/FLUX.2-dev
2. https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9b-fp8
3. https://huggingface.co/google/gemma-3-12b-pt

Without this, the downloader will fail with `403 Forbidden` on those repos.

### Step 3: Clone + run the interactive installer

```bash
git clone https://github.com/AEON-7/comfyui-aeon-spark.git
cd comfyui-aeon-spark
./setup.sh
```

When prompted: paste the HF token from Step 1. Choose `:latest` (default) for auto-download. The script writes `.env` (chmod 600), launches `docker compose up`, and starts the model download.

### Step 4: Wait for first-start download (~45 min, 285 GB)

The container streams its progress to its log:

```bash
docker logs -f comfyui-spark
```

When you see `Launching ComfyUI on port 8188` followed by no errors, the stack is up.

### Step 5: Open ComfyUI

Browser: **`http://<host-ip>:8188`** (use `localhost` if running on your local machine).

That's it. Generate an image, generate a video, generate music. Default workflows are pre-loaded under "Workflows" in the left sidebar.

---

## 🆘 Troubleshooting — symptom → exact fix

If something goes wrong, find the symptom in the table below and run the fix. Most problems have one-line solutions.

| Symptom | Likely cause | Exact fix |
|---|---|---|
| `setup.sh: command not found` or `Permission denied` | Script not executable | `chmod +x setup.sh sync.sh && ./setup.sh` |
| `docker: command not found` | Docker Engine not installed | `curl -fsSL https://get.docker.com \| sh && sudo systemctl enable --now docker` |
| `Error response from daemon: could not select device driver "nvidia"` | NVIDIA Container Toolkit missing | `sudo apt install -y nvidia-container-toolkit && sudo systemctl restart docker` |
| `403 Forbidden` while downloading | HF gated models not accepted | Redo Step 2 above. Click "Agree and access" on each gated repo while logged in as the same HF user whose token you're using. |
| `401 Unauthorized` while downloading | HF token wrong, expired, or missing Read scope | Regenerate token at https://huggingface.co/settings/tokens with Read scope, then `nano .env`, paste new token, `docker compose restart` |
| ComfyUI unreachable on `:8188` from another machine | Firewall blocking port | `sudo ufw allow 8188/tcp` (or open in cloud provider's security group) |
| `OOM` / out-of-memory during generation | Too many models loaded simultaneously | Click "Free memory" in ComfyUI's right sidebar. If it persists, `docker compose restart`. |
| `disk full` mid-download | Less than 350 GB free on workspace volume | `df -h` to confirm, then either free space or set `COMFY_WORKSPACE` in `.env` to a path on a larger disk and `docker compose down && docker compose up -d` |
| Model download stalls at 0% for >5 minutes | HF Hub rate-limited or your network blocked | `docker logs comfyui-spark \| tail` to see exact URL, retry with `docker compose restart` |
| Want to update / get new workflows / new models | You already deployed once | **Run `./sync.sh`**. Do NOT re-clone or re-run `setup.sh` — they would re-download everything. `sync.sh` only fetches the delta. |
| Want to start completely fresh (different host, etc.) | Need clean state | `docker compose down -v && rm -rf workspace && ./setup.sh` (note: `-v` deletes the workspace volume — your downloaded models will be re-fetched) |

For deeper agent-level troubleshooting, see [§6 in AGENTS.md](AGENTS.md#6--common-failure-patterns-and-exact-fixes).

---

### Tag matrix

| Tag | Image size | What's inside | When to use |
| --- | --- | --- | --- |
| **`latest`** / `full` / `bf16-flux2-ltx2.3` / `cu130-sm121a` | **17 GB** | code + downloader; on first start the downloader pulls **~285 GB of weights** into your workspace volume using **your HF_TOKEN** | default — you have an HF account, you just want it to work |
| **`slim`** / `base` | **17 GB** | code only, **no auto-download** | when you want to pick every model individually via the in-UI Manager, or when you want full control / fine-grained license consent |

Both variants ship the same code, custom nodes, and workflows. The difference is one runs the bundled downloader on first start; the other waits for you to install models via the UI.

**No image variant ever ships pre-embedded weights.** That keeps every model's license cleanly the responsibility of the user pulling the file from HuggingFace under their own account. We never act as a redistributor of model weights.

### License notes (read before commercial use)

| Model | Where it lives | License | Notes |
| --- | --- | --- | --- |
| FLUX.2-dev | [black-forest-labs/FLUX.2-dev](https://huggingface.co/black-forest-labs/FLUX.2-dev) | [FLUX.2 [dev] Non-Commercial](https://huggingface.co/black-forest-labs/FLUX.2-dev/blob/main/LICENSE.md) | research / non-commercial only by default |
| FLUX.2-klein-base-9b-fp8 | [black-forest-labs/FLUX.2-klein-base-9b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9b-fp8) | BFL Klein, **gated** | must "Agree and access" on HF before HF_TOKEN can download it |
| Mistral-Small-3 (Flux 2 text encoder) | [Comfy-Org/flux2-dev](https://huggingface.co/Comfy-Org/flux2-dev) | [Mistral Research License](https://mistral.ai/terms#research-license) | research use |
| Gemma-3 (LTX 2.3 text encoder) | [Comfy-Org/ltx-2](https://huggingface.co/Comfy-Org/ltx-2) | [Gemma Terms of Use](https://ai.google.dev/gemma/terms) | attribution + restrictions |
| LTX 2.3 | [Lightricks/LTX-2.3](https://huggingface.co/Lightricks/LTX-2.3) | [Lightricks Open Weights](https://huggingface.co/Lightricks/LTX-2.3/blob/main/LICENSE) | mostly permissive |
| ACE-Step v1.5 | [Comfy-Org/ace_step_1.5_ComfyUI_files](https://huggingface.co/Comfy-Org/ace_step_1.5_ComfyUI_files) | [ACE-Step](https://huggingface.co/ACE-Step/ACE-Step-v1) | see model card |
| Qwen 0.6B / 4B / 3-8B | Comfy-Org repacks of [Qwen/Qwen3-*](https://huggingface.co/Qwen) | Apache 2.0 / Qwen RL | mostly permissive |
| huihui-ai abliterated weights | [huihui-ai](https://huggingface.co/huihui-ai) | inherits parent license | derivatives |

[**▶ QuickStart**](#quickstart) · [**Why DGX Spark**](#why-this-image-exists--target-system) · [**Hardware Compatibility**](#hardware-compatibility-matrix) · [**What's Bundled**](#whats-bundled) · [**Optimization Story**](#optimization-story) · [**🤖 AI-Agent deployment guide → AGENTS.md**](AGENTS.md)

---

## Quickstart

### Easiest: interactive setup (recommended)

```bash
git clone https://github.com/AEON-7/comfyui-aeon-spark.git
cd comfyui-aeon-spark
./setup.sh
```

The script walks you through getting an HF token, accepting the gated-model licenses, picking your image variant, and launching the stack. It hides the token as you paste it (no echo to scrollback) and writes a `chmod 600` `.env`. Skip ahead to [What's bundled](#whats-bundled) once it finishes.

### Already deployed? Sync new workflows + models without redeploy

```bash
cd comfyui-aeon-spark
./sync.sh
```

Pulls the latest image, refreshes the in-repo workflows and downloader script, shows a **diff** of what's new (workflows, model entries), and only fetches the delta. Idempotent — files already on disk are skipped, your Manager-installed nodes are preserved, your saved workflows untouched.

Useful flags:
- `./sync.sh --yes` — non-interactive (for agents / cron)
- `./sync.sh --no-models` — refresh workflows & scripts but skip model downloads (saves bandwidth)

If you'd rather do the initial deploy manually, the same steps in long form:

### 1. Get a HuggingFace token (5 min, free)

Required for `:latest` (auto-download). Optional for `:slim`.

1. Sign up / sign in at [huggingface.co](https://huggingface.co/join).
2. Go to **[Settings → Access Tokens](https://huggingface.co/settings/tokens)**.
3. Click **"+ Create new token"** → name it (e.g. `dgx-spark`) → **Token type: Read** → Create.
4. Copy the token. It looks like `hf_AbCd1234...`.

### 2. Accept gated-model licenses (3 click-throughs)

A few of the bundled-by-default models are gated by their authors. Open each link, sign in, and click **"Agree and access repository"**:

- ✅ **[FLUX.2-dev](https://huggingface.co/black-forest-labs/FLUX.2-dev)** — required for workflow 01 (Flux 2 t2i)
- ✅ **[FLUX.2-klein-base-9b-fp8](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9b-fp8)** — required for workflow 08 (Klein 9B)
- ✅ **[FLUX.2-small-decoder](https://huggingface.co/black-forest-labs/FLUX.2-small-decoder)** — Flux 2 VAE used by canonical templates

(Mistral, Gemma, LTX 2.3, Qwen, ACE-Step are not gated — your token can pull them right away once you sign in once.)

### 3. Launch

```bash
mkdir -p ~/comfyui-spark/workspace && cd ~/comfyui-spark
cat > .env <<'EOF'
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
cat > docker-compose.yml <<'EOF'
services:
  comfyui:
    image: ghcr.io/aeon-7/comfyui-aeon-spark:latest
    container_name: comfyui-spark
    runtime: nvidia
    deploy: { resources: { reservations: { devices: [{ driver: nvidia, count: all, capabilities: [gpu] }] } } }
    ports: ["8188:8188"]
    environment:
      HF_TOKEN: "${HF_TOKEN:-}"
    volumes: ["./workspace:/workspace/ComfyUI"]
    shm_size: "32gb"
    ipc: host
    ulimits: { memlock: -1, stack: 67108864 }
    restart: unless-stopped
EOF
docker compose up -d && docker compose logs -f comfyui
```

First start downloads ~285 GB of models. At ~95 MB/s expect ~50 minutes;
look for `download summary: 35 ok, 0 failed` then `Launching ComfyUI on
port 8188`. (If you skipped accepting the BFL Klein license you'll see
`34 ok, 1 failed` — that's expected; workflow 08 needs Klein, others don't.)

Then open `http://<spark-host>:8188`.

### Or — `:slim` mode (no auto-download, you pick everything)

```bash
sed -i 's|comfyui-aeon-spark:latest|comfyui-aeon-spark:slim|' docker-compose.yml
docker compose up -d
```

ComfyUI starts in seconds with zero models on disk. Open the **Manager** in the top bar, click **"Install Missing Models"** when you load a workflow, or open the **Asset Browser** to install any specific model. Every download goes server-side into `./workspace/models/<directory>/` — never to your browser. Set `HF_TOKEN` if you plan to install gated models.

### Adding more gated models later

If you load a community workflow that needs a gated model:

1. Open the model's HF page → click **Agree and access**
2. The same `HF_TOKEN` you set up earlier already works (no re-login needed)
3. Click **Install** in the ComfyUI UI

If you need to expand `HF_TOKEN`'s permissions (e.g., the model is in an org you need access to), regenerate it on the [tokens page](https://huggingface.co/settings/tokens) and update `.env`, then `docker compose up -d` to pick it up.

---

## Why this image exists / target system

### Primary target: NVIDIA DGX Spark (GB10)

DGX Spark is the desktop / workstation Grace-Blackwell platform NVIDIA
ships with the **GB10 SoC** — Grace ARM CPU + Blackwell GPU on a coherent
unified-memory fabric. Spec at a glance:

| Spec | Value |
| --- | --- |
| GPU | **GB10 Blackwell** |
| Compute capability | **sm_121 / sm_121a** (datacenter Blackwell variant) |
| Tensor cores | 5th-gen with native **NVFP4** support |
| Architecture | ARM64 (Grace) + Blackwell (GPU), coherent unified memory |
| Memory | **128 GB LPDDR5X** unified across CPU+GPU |
| Driver / CUDA | NVIDIA 580.x / **CUDA 13.0** |
| OS | Ubuntu 24.04 (DGX OS) |

This is **a different compute capability from every other Blackwell
part** shipping today. NVCC support for `sm_121` first landed in
**CUDA 13.0** — neither CUDA 12.8 (max sm_120) nor any prior toolchain
can emit code for it. Everything in this image was specifically built
to take advantage of that:

| Concern | Stock setup | This image |
| --- | --- | --- |
| CUDA toolchain | CUDA 12.x (max sm_120) | **CUDA 13.0.2** — first toolchain that emits sm_121 SASS |
| PyTorch | x86 / cu128 / no sm_121 PTX | **2.9.1+cu130 ARM64**, sm_120 SASS + compute_120 PTX (forward-JITs to sm_121 on first kernel call, then cached) |
| Attention | xformers / FA3 (no sm_121) | **SageAttention v3 compiled from source for `sm_121a` + `sm_121`** — no JIT cost, no fallback to slow SDPA |
| Memory model | discrete-GPU defaults | **Grace-Blackwell unified-memory tuned** — pinned pages off, async offload on, expandable segments |
| Triton | torch.compile crashes on sm_121 | **Triton present, torch.compile explicitly disabled** so dynamo doesn't trip |
| NVFP4 | not exposed | CUTLASS NVFP4 GEMMs via CUDA 13 — `*_fp4_mixed` weights take the accelerated path automatically |
| Manager | manual ltdrdata install | Both **ltdrdata custom node** + the new **`comfyui-manager` pip pkg** with `--enable-manager` |
| Models | bring your own | **35 artifacts auto-pulled** on first start (33 named files + 2 abliterated full-LLM snapshots): Flux 2, LTX 2.3, ACE-Step + abliterated swap-ins |

### What "optimized for DGX Spark" actually means here

The Spark unified-memory fabric is **not** like a discrete GPU + system
RAM. There's one physical pool, addressable from both CPU and GPU,
coherent at cacheline granularity. That changes which optimizations
help and which actively hurt:

- **Pinned host memory hurts.** Pinning host pages on a discrete GPU
  enables zero-copy DMA. On Grace-Blackwell, the pages are *already*
  GPU-addressable, and pinning forces an unnecessary buffer-management
  path. We disable it (`--disable-pinned-memory`).
- **`--gpu-only` hurts.** It tries to keep weights "on the GPU side"
  that doesn't really exist as a separate place. We don't use it.
- **VRAM utilization caps at 0.88.** Pushing past it triggers thrashing
  on the unified pool. We default to `--reserve-vram 2.0` to leave OS
  scratch within the cap.
- **`torch.compile` / Inductor / dynamo are off.** Triton 3.5/3.6 don't
  yet emit working SASS for sm_121a. Code paths that go through
  `torch.compile` JIT-fail or generate broken kernels. SageAttention
  covers the throughput we'd otherwise want from `torch.compile`.
- **NVFP4 happens at the GEMM level, not via a flag.** When you load
  `mistral_3_small_flux2_fp4_mixed.safetensors` instead of the BF16
  variant, the model's matmul ops dispatch to **CUDA 13's CUTLASS NVFP4
  GEMMs**, which on sm_121a use 5th-gen tensor-core FP4 paths. No Marlin
  involved — Marlin is a Hopper SXM5 codepath that mis-fires on GB10.

This image bakes in those choices so a user typing
`docker compose up -d` ends up on the optimal path without having to
read every Spark-specific gotcha.

---

## Hardware compatibility matrix

This image was *built for* sm_121a, but Blackwell SASS is forward-JIT
compatible from the compute_120 PTX shipped in the PyTorch wheel — and
SageAttention's sm80/sm89 fallbacks cover earlier arches. Practical
behavior across NVIDIA platforms:

| Platform | Compute cap | OS / Arch | Will it run? | Performance vs Spark | Notes |
| --- | --- | --- | --- | --- | --- |
| **DGX Spark (GB10)** | **sm_121a** | **ARM64 / Ubuntu 24.04** | **✅ Native target** | **100%** (reference) | Everything pre-compiled for this. SageAttention v3 hits sm_121a SASS directly, NVFP4 via CUTLASS, BF16 free. |
| **DGX Station (anticipated GB10/GB100)** | sm_121 / sm_100 | ARM64 | ✅ | ~95-105% | Same generation Blackwell datacenter, near-identical paths. May want recompiled SageAttention if exact arch differs. |
| **Jetson Thor (T5000)** | sm_101 (Blackwell) | ARM64 / L4T | ⚠️ Probably needs rebuild | ~70-80% | ARM64 + Blackwell, but L4T toolchain quirks; SageAttention rebuild recommended for sm_101. Memory budget tighter (64 GB). |
| **GB200 NVL** (Blackwell datacenter) | sm_100a | ARM64 (Grace) | ✅ with caveats | ~150-200%+ | Way more memory (192/384 GB HBM3e), much more compute. SageAttention's sm89 fallback works; recompile for sm_100a unlocks the full path. |
| **B100 / B200 PCIe** | sm_100a | x86 / ARM | ✅ with caveats | ~150-200%+ | Same as above. Image is ARM64; build an x86 variant or run via QEMU/multi-arch buildx. |
| **RTX PRO 6000 Blackwell** (workstation) | sm_120 | x86 | ✅ with rebuild | ~80-100% | Same Blackwell family, sm_120 not sm_121. PTX→SASS JIT works at first run. SageAttention rebuild recommended. Image is ARM64 — pull the x86 variant or build locally. |
| **RTX 5090 / 5080** (consumer Blackwell) | sm_120 | x86 | ⚠️ Needs x86 rebuild | ~85-95% | Same compute family, x86 ABI. Rebuild image with `--platform linux/amd64`. SageAttention v3 has sm_120 wheels. |
| **H100 / H200** (Hopper) | sm_90 | x86 / ARM | ⚠️ Works, suboptimal | ~60-80% | SageAttention v3 hits the proper sm_90 path; CUTLASS FP4 has a Hopper variant but it's slower than Blackwell. NVFP4 weights still dispatch to working kernels but not the 5th-gen tensor cores. Rebuild for x86. |
| **L40S / RTX 6000 Ada** (Ada Lovelace) | sm_89 | x86 | ⚠️ Works, no NVFP4 | ~50-70% | SageAttention's sm89 path works for attention. NVFP4 weights fall through to BF16 path. Use BF16 variants of all models. Rebuild for x86. |
| **A100 / A30** (Ampere) | sm_80 | x86 | ⚠️ Works, no NVFP4, no FP8 | ~30-50% | SageAttention sm80 path works. No FP8/FP4 hardware support. Stick to BF16 weights, plenty of VRAM (40/80 GB) makes that fine. Rebuild for x86. |
| **RTX 4090 / Ada workstation** | sm_89 | x86 | ⚠️ VRAM-limited | varies | Workflow files load fine; some Flux 2 / LTX 2.3 models won't fit in 24 GB without aggressive offload. Use the FP8/FP4 variants. Rebuild for x86. |
| **RTX 3090 / Ampere workstation** | sm_86 | x86 | ⚠️ VRAM-limited, slower | varies | Similar to 4090 but no FP8 path. Strictly BF16 + offload + GGUF. Rebuild for x86. |

### TL;DR cross-platform

- **Other Grace-Blackwell systems** (DGX Station, GB200, future Spark
  variants): pulls and runs out of the box, often faster than Spark.
- **Consumer Blackwell** (RTX 5090/5080): great fit, just needs an x86
  rebuild — `docker buildx build --platform linux/amd64 -t comfyui-aeon-spark:x86 .`.
- **Hopper / Ada / Ampere**: works but progressively suboptimal — the
  NVFP4 hardware path is what makes Spark special here, and only
  Blackwell has it. Use BF16 variants on these and accept that you're
  not getting the 5th-gen tensor-core acceleration.
- **AMD / Intel / Apple Silicon**: not supported. The image assumes
  CUDA 13 and a Blackwell-class compute capability.

---

## What's bundled

### Runtime stack

| Component | Version / source |
| --- | --- |
| Base | `nvidia/cuda:13.0.2-devel-ubuntu24.04` (ARM64) |
| Python | 3.12.3 |
| PyTorch | **2.9.1+cu130** |
| Triton | 3.5.1 (kept available; `torch.compile` disabled by env) |
| **SageAttention** | **v3 main, compiled with `-gencode arch=compute_121a,code=sm_121a`** |
| ComfyUI | latest `master` (0.20.1 at build time) |
| ComfyUI-Manager | both ltdrdata custom node + the new **`comfyui-manager` pip pkg**, `--enable-manager` set by default |
| Diffusers | 0.37.1 |
| Transformers | 5.7.0 |
| HuggingFace Hub | 1.12.0 + `hf-transfer` enabled |
| GGUF runtime | `gguf` >= 0.13 + sentencepiece + protobuf |
| **Total backend nodes registered** | **~1728** (Comfy core + 16 bundled custom-node packs) |

### Bundled services

The compose stack ships **two services**:

- **`comfyui`** — main UI on `:8188`
- **`ollama`** — LLM sidecar, auto-pulls `gemma3:4b` (~3 GB, swap via `OLLAMA_PRELOAD_MODEL`). Used by workflow 09 (AceStep audio) for prompt expansion. Reachable from `comfyui` as `http://ollama:11434`.

`ollama:11434` isn't exposed to the host by default — it's an internal-only service. If you want to use it from other clients on your LAN, add `ports: ["11434:11434"]` to the ollama service in `docker-compose.yml`.

### Server-side model downloads (not browser downloads!)

This image ships **two** independent paths that both route model downloads to the **server**:

1. **Manager → Install Missing Models / Asset Browser** — uses the `comfyui-manager` pip pkg's `/v2/manager/queue/batch` endpoint. Downloads land in `./workspace/models/<directory>/` on the server.
2. **Workflow Overview → Errors → Missing Models → Download all / Download** — core ComfyUI 0.20's new built-in panel. **By default, core ComfyUI fires `window.open(url)` here, which downloads to the client machine.** That's the wrong behavior for remote-accessed Sparks.
   - This image bundles `aeon-server-side-downloads` (a JS-only custom-node pack) that intercepts those clicks and re-routes them through Manager's queue API. After the intercept, you'll see a toast: *"Queueing N file(s) for server-side download…"*. The file lands in your workspace volume on the server.
   - Falls back transparently to the browser download if Manager isn't reachable, so it never breaks worse than upstream.

`--enable-assets` and `--enable-manager` are on by default. Sources of model URLs (read in this order):
1. `properties.models[]` arrays on workflow loader nodes (canonical Comfy templates have these wired)
2. `download_models.py` runs at first start to pre-fetch the bundled set (`:latest` only)
3. ComfyUI Manager's catalog (browse → install for any community model)

### Bundled ComfyUI custom node packs

| Pack | Why |
| --- | --- |
| **ComfyUI-Manager** (ltdrdata) | classic node/model manager |
| **ComfyUI-LTXVideo** (Lightricks) | 94 official LTX-2 nodes |
| **ComfyUI-GGUF** (city96) | GGUF text encoders + DiTs |
| **ComfyUI_essentials** (cubiq) | image utilities |
| **rgthree-comfy** | workflow ergonomics (48 nodes) |
| **ComfyUI-Custom-Scripts** (pythongosssss) | favorites, autocomplete, etc. |
| **ComfyUI-KJNodes** (kijai) | huge collection incl. GetNode/SetNode virtual links |
| **ComfyUI-Frame-Interpolation** (Fannovel16) | RIFE / FILM video upscaling |
| **ComfyUI-Crystools** | on-canvas perf monitor |
| **ComfyUI-Easy-Use** (yolain) | simplified flux/ltx/sd flows |
| **ComfyUI-RES4LYF** (ClownsharkBatwing) | advanced samplers including the `ClownSampler_Beta` family — required by Lightricks's distilled LTX workflow |
| **ComfyUI-VideoHelperSuite** (Kosinkadink) | video I/O nodes |
| **ComfyUI-Ollama** (stavsap) | Ollama LLM-prompting nodes (used by ACE-Step Ancient_Sufi workflow) |
| **ComfyUI-Detail-Daemon** (Jonseed) | `MultiplySigmas`, `LyingSigmaSampler`, etc. |
| **aeon-server-side-downloads** (in-tree) | JS-only extension that intercepts the new ComfyUI 0.20+ "Workflow Overview → Missing Models → Download" buttons and routes the download server-side via Manager's queue API, so files land in your workspace volume on the **server**, not in your browser on the **client** machine. Critical for remote-accessed Sparks. |
| **ComfyUI-PromptRelay** (kijai) | Timeline-based per-second prompt control for video — change descriptions throughout the sequence (used by `10_ltx2.3_prompt_relay`). |

### Models auto-downloaded on first start (~285 GB)

#### Flux 2 Dev (Black Forest Labs / Comfy-Org pre-split)
- DiT (`flux2_dev_fp8mixed.safetensors`, 35.5 GB)
- Two VAEs (`flux2-vae.safetensors`, `full_encoder_small_decoder.safetensors`)
- Mistral-3 Small text encoder in **BF16** (35.6 GB) and **NVFP4-mixed** (12.3 GB)
- Two Turbo LoRAs (canonical + alt filename)

#### LTX 2.3 22B (Lightricks)
- BF16 transformer-only DiT (42 GB) and FP8 transformer-only DiT (23.5 GB)
- FP8 fused checkpoint (29 GB) — used by Lightricks's canonical workflows
- Text projection layer, video VAE, audio VAE, tiny preview VAE
- Dynamic distilled LoRA + canonical 384-rank distilled LoRA
- Spatial upscaler x2 v1.1 + temporal upscaler x2 v1.0

#### Gemma-3 (LTX 2.3 text encoder, Comfy-Org split)
- Gemma-3 12B IT in **BF16** (24.4 GB) and **NVFP4-mixed** (9.4 GB)

#### ACE-Step v1.5 (Ancient_Sufi audio-generation workflow)
- ACE-Step XL Turbo DiT BF16 (9.97 GB)
- Qwen 0.6B + Qwen 4B text encoders
- 1D audio VAE

#### Abliterated text-encoder paths
- Two abliterated **LoRAs** for the Gemma encoder (heretic + alt)
- Two **full HF-format snapshots** for direct swap-in: huihui-ai
  Mistral-Small-3.2 24B abliterated + huihui-ai Gemma-3 12B IT abliterated
- Set `SKIP_ABLITERATED=1` to skip the ~70 GB snapshots and only fetch the
  smaller LoRA path.

### Default workflows seeded into `user/default/workflows/`

| File | What it does |
| --- | --- |
| `01_flux2_text_to_image.json` | Comfy canonical Flux 2 Dev t2i (subgraph workflow) |
| `02_ltx2.3_T2V_I2V_distilled.json` | Lightricks's official LTX-2.3 single-stage distilled T2V/I2V (uses `ClownSampler_Beta`, abliterated Gemma LoRA, FP8 checkpoint, distilled-lora-384, both upscalers) |
| `03_ltx2.3_T2V_two_stage.json` | Lightricks's two-stage T2V (cleaner motion) |
| `04_ltx2.3_image_to_video.json` | Comfy canonical LTX-2.3 I2V |
| `05_ltx2.3_first_last_frame_to_video.json` | Comfy canonical LTX-2.3 first-frame/last-frame-to-video |
| `07_ltx2.3_id_lora.json` | Comfy canonical LTX-2.3 with identity-LoRA wiring |
| `08_flux2_klein_9b_text_to_image.json` | Flux 2 Klein 9B variant t2i |
| `09_acestep_ancient_sufi_xl.json` | ACE-Step v1.5 XL Turbo audio with Ollama prompt-expansion |
| `10_ltx2.3_prompt_relay.json` | LTX 2.3 22B distilled-1.1 fp8 + Kijai's [ComfyUI-PromptRelay](https://github.com/kijai/ComfyUI-PromptRelay) — timeline-based per-second prompt control for video |

---

## Optimization story

### Compile-time work that's already been done

1. **SageAttention v3 compiled inside the image** with explicit
   `-gencode=arch=compute_121a,code=sm_121a -gencode=arch=compute_121,code=sm_121`.
   This produces Blackwell-datacenter SASS for `_qattn_sm80`, `_qattn_sm89`,
   and `_fused`. **Zero JIT cost on first generation.**
2. **PyTorch 2.9.1+cu130** ships sm_120 SASS plus compute_120 PTX. On
   Spark the PTX gets JIT-compiled to sm_121a SASS the first time a kernel
   runs, then cached in `~/.nv/ComputeCache`. Forward-compat is the path
   NVIDIA recommends for pre-release silicon.
3. **CUDA 13.0.2 toolchain** in the build image is the first NVCC release
   that emits sm_121 — CUDA 12.x literally cannot.
4. **All 16 custom-node `requirements.txt` resolved at build time**, so
   you don't pay the dependency-resolve tax on every container start.

### Runtime tuning that ships by default

| Knob | Setting | Why |
| --- | --- | --- |
| `--use-sage-attention` | on | fastest sm_121a attention path |
| `--bf16-unet --bf16-vae --bf16-text-enc` | on | Spark's 128 GB unified pool means BF16 is free; NVFP4 weights still take their hardware path automatically when loaded |
| `--disable-pinned-memory` | on | Grace-Blackwell coherent fabric performs *worse* with pinned host pages |
| `--reserve-vram 2.0` | 2 GB | leaves OS scratch on the unified pool — Spark caps utilization at 0.88 |
| `--enable-manager` | on | wires the new in-frontend Manager dialog to the `comfyui-manager` pip pkg |
| `--enable-cors-header` | on | external clients (mobile UIs, automation) can hit the API |
| `TORCH_COMPILE_DISABLE=1` | on | Triton doesn't yet emit working SASS for sm_121a |
| `CUDA_MODULE_LOADING=EAGER` | on | avoids the lazy-load stall ComfyUI hits on first model swap |
| `PYTORCH_ALLOC_CONF=expandable_segments:True` | on | reduces fragmentation when juggling 35 GB DiTs |
| `CUDA_DEVICE_MAX_COPY_CONNECTIONS=4` | tuned | matches the GB10 copy-engine count |

### Why no FlashAttention

FA2 / FA3 / FA4 don't ship sm_121 kernels (FA4 only does sm_100; FA2/3
stop at sm_90). SageAttention v3 covers the same surface plus quantized
variants the FA family doesn't have. The image deliberately omits
FlashAttention rather than waste size on a wheel that would silently fall
back to PyTorch SDPA at runtime.

### Why NVFP4 is automatic

There's no "enable NVFP4" flag. The weights are FP4 — when ComfyUI's
`CLIPLoader` (or `UNETLoader`) loads `*_fp4_mixed.safetensors`, the
matmul ops dispatch to **CUDA 13's CUTLASS NVFP4 GEMMs**, which on
sm_121a use the 2nd-gen tensor-core FP4 path.

To switch any workflow from BF16 (best quality) to NVFP4 (max throughput),
swap one widget on the loader from e.g.
`mistral_3_small_flux2_bf16.safetensors` →
`mistral_3_small_flux2_fp4_mixed.safetensors`.

### Persistent volume layout

```
workspace/                           ← single host-mounted volume
├── models/                          ← 285 GB of pre-staged weights
│   ├── diffusion_models/            ← Flux 2 + LTX 2.3 + ACE-Step DiTs
│   ├── checkpoints/                 ← LTX 2.3 FP8 fused checkpoint
│   ├── text_encoders/               ← Mistral, Gemma, Qwen
│   │   └── abliterated/             ← + huihui-ai full HF dirs
│   ├── vae/  loras/  latent_upscale_models/
│   └── ... all standard ComfyUI subdirs
├── custom_nodes/                    ← 16 bundled + anything Manager adds
├── output/                          ← generated images, videos, audio
├── input/                           ← reference inputs
├── user/default/workflows/          ← 8 pre-seeded workflows
└── temp/                            ← scratch
```

Wipe the container, rebuild the image, mount the same `workspace/`, and
everything boots in seconds with the same models, settings,
Manager-installed nodes, and saved workflows.

---

## Tuning cheat sheet

| Goal | Switch to | Why |
| --- | --- | --- |
| Maximum quality | leave defaults — BF16 path is default | Spark unified memory is plentiful |
| Maximum throughput | swap CLIPLoader's encoder file from `*_bf16.safetensors` → `*_fp4_mixed.safetensors` | takes the CUTLASS NVFP4 GEMM path on sm_121a 2nd-gen tensor cores |
| Fewer-step Flux 2 | drop in `Flux2TurboComfyv2.safetensors` LoRA, set steps to 4–8 | Turbo LoRA is pre-staged |
| Fast LTX 2.3 | use `02_ltx2.3_T2V_I2V_distilled` as-is — loads `ltx-2.3-22b-distilled-lora-384` at 8 steps | bundled |
| No abliteration (LTX 2.3) | bypass the `LoraLoader` for `gemma-3-12b-it-abliterated_*` in workflow 02 | one click |
| Audio generation | open `09_acestep_ancient_sufi_xl` | ACE-Step + Ollama prompt expansion |

---

## What's *not* included (and why)

- **xformers** — no sm_121 wheel exists; deliberately skipped on ARM64.
- **FlashAttention 2/3/4** — no sm_121 support yet; SageAttention v3
  covers the same surface.
- **bitsandbytes** — depends on FA-style kernels not on sm_121; replace
  with GGUF (already bundled) or NVFP4 weights (already bundled).
- **TensorRT engines** — RT engines aren't portable across compute
  capabilities; building them inside the container would defeat the
  cold-start-ready goal. Run TRT engine builds yourself if you need them.
- **Frontend node editor extras (3D / animation suites)** — install via
  Manager so they live in your volume, not the image.

---

## Adding more workflows

Drop the `.json` into `~/comfyui-spark/workspace/user/default/workflows/` —
no rebuild, no restart. The UI auto-discovers it on the next browser
refresh.

To bundle a workflow as a default for *future* fresh starts of this image,
fork this repo, drop the file into `workflows/`, and rebuild — the
incremental rebuild touches only one COPY layer (~5–15 seconds).

## Adding more custom nodes

Use the in-UI Manager (button in the top bar). Installs land in
`workspace/custom_nodes/` and survive container recreations.

## Adding more models

Drop files into the appropriate `workspace/models/<subdir>/`. ComfyUI's
loaders auto-rescan — refresh the loader's dropdown in the UI.

## Updating ComfyUI

```bash
docker compose pull             # grab the latest :latest tag
docker compose up -d            # recreate; volume keeps everything
```

## Sharing the GPU with vLLM

Spark has a single GPU. Stop one before starting the other:

```bash
docker stop vllm-aeon-ultimate-v2 && docker compose up -d   # ComfyUI
# or
docker compose down && docker start vllm-aeon-ultimate-v2   # back to vLLM
```

---

## Repo layout

```
├── Dockerfile           # multi-stage build with SageAttention compile
├── docker-compose.yml   # tuned for Grace-Blackwell unified memory
├── entrypoint.sh        # workspace bootstrap + model downloader + launch
├── download_models.py   # 28-artifact resumable downloader
├── workflows/           # 8 .json files baked into the image
├── .env.example         # HF_TOKEN + tuning flags
├── README.md            # this file
├── AGENTS.md            # deployment guide for AI agents (Claude, Copilot, etc.)
├── WRITEUP.md           # extended writeup (more detail than README)
└── QUICKSTART.md        # 3-command run + troubleshooting
```

## Deploying via an AI agent

If you're handing this to an AI agent (Claude, Copilot, Cursor, etc.) to deploy on a Spark you have SSH access to, point it at [`AGENTS.md`](AGENTS.md). It's structured top-to-bottom with pre-flight checks, single-block deployment commands, post-deploy validation, exact-fix matrices for common failures, hard "do not" guardrails, and a standard report-back template.

## License

MIT. Bundled custom-node packs and model weights retain their respective
upstream licenses (Apache 2.0 / MIT / FLUX Non-Commercial / etc).
**The Flux 2 Dev model is under Black Forest Labs's Non-Commercial
license — review before commercial use.**

## Build / push reference (only if you're forking)

The published image at `ghcr.io/aeon-7/comfyui-aeon-spark` is the canonical
artifact and is what `docker compose pull` grabs. If you want to fork and
publish your own variant under a different namespace:

```bash
git clone https://github.com/AEON-7/comfyui-aeon-spark.git
cd comfyui-aeon-spark

# docker compose build tags the local image as
# ghcr.io/aeon-7/comfyui-aeon-spark:latest (per docker-compose.yml).
# Re-tag and push under your own namespace:
docker compose build              # ~3 min on Spark with ccache hot
docker tag ghcr.io/aeon-7/comfyui-aeon-spark:latest \
           ghcr.io/<your-namespace>/comfyui-aeon-spark:custom
docker push ghcr.io/<your-namespace>/comfyui-aeon-spark:custom
```

For an x86 fork (RTX 5090/5080 consumer Blackwell):

```bash
DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 \
  --build-arg TORCH_CUDA_ARCH_LIST="12.0" \
  -t ghcr.io/<your-namespace>/comfyui-aeon-spark:cu130-x86 .
```

---

*Built and maintained for the [DGX Spark](https://www.nvidia.com/en-us/products/workstations/dgx-spark/) AI workstation. Pairs naturally with [vllm-aeon-ultimate](https://github.com/AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4-DFlash) for LLM serving on the same hardware.*

---

## ☕ Support the work

AEON-7 models, drafters and tools are built and trained independently, on my own hardware. If they're useful to you, please consider supporting development:

**[Become a member on Patreon → patreon.com/cw/AeonForge7/membership](https://www.patreon.com/cw/AeonForge7/membership)**

Milestones unlock bigger work: reaching **500 paid supporters** will fund fine-tuning larger models and bigger project releases. Supporters also get early access to new releases, such as the [AEON DFlash2 drafter](https://www.patreon.com/AeonForge7/posts/early-access-for-171543895).

If this release has been useful, tips are deeply appreciated — they go directly toward more compute, more models, and more open releases.

<table align="center">
  <tr>
    <td align="center" width="50%">
      <strong>₿ Bitcoin (BTC)</strong><br/>
      <img src="https://raw.githubusercontent.com/AEON-7/AEON-7/main/assets/qr/btc.png" alt="BTC QR" width="200"/><br/>
      <sub><code>bc1q09xmzn00q4z3c5raene0f3pzn9d9pvawfm0py4</code></sub>
    </td>
    <td align="center" width="50%">
      <strong>Ξ Ethereum (ETH)</strong><br/>
      <img src="https://raw.githubusercontent.com/AEON-7/AEON-7/main/assets/qr/eth.png" alt="ETH QR" width="200"/><br/>
      <sub><code>0x1512667F6D61454ad531d2E45C0a5d1fd82D0500</code></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <strong>◎ Solana (SOL)</strong><br/>
      <img src="https://raw.githubusercontent.com/AEON-7/AEON-7/main/assets/qr/sol.png" alt="SOL QR" width="200"/><br/>
      <sub><code>DgQsjHdAnT5PNLQTNpJdpLS3tYGpVcsHQCkpoiAKsw8t</code></sub>
    </td>
    <td align="center" width="50%">
      <strong>ⓜ Monero (XMR)</strong><br/>
      <img src="https://raw.githubusercontent.com/AEON-7/AEON-7/main/assets/qr/xmr.png" alt="XMR QR" width="200"/><br/>
      <sub><code>836XrSKw4R76vNi3QPJ5Fa9ugcyvE2cWmKSPv3AhpTNNKvqP8v5ba9JRL4Vh7UnFNjDz3E2GXZDVVenu3rkZaNdUFhjAvgd</code></sub>
    </td>
  </tr>
</table>

> **Ethereum L2s (Base, Arbitrum, Optimism, Polygon, etc.) and EVM-compatible tokens** can be sent to the same Ethereum address.
