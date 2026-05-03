#!/usr/bin/env python
"""
Download Flux 2 Dev + LTX 2.3 (full) + abliterated text encoders into the
ComfyUI persistent workspace. Resumable via huggingface_hub.

Models targeted for DGX Spark unified memory (BF16 default, NVFP4 alts cached
for users that want max throughput on the sm_121a CUTLASS NVFP4 path).
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Iterable

from huggingface_hub import hf_hub_download, snapshot_download
from huggingface_hub.utils import HfHubHTTPError

logging.basicConfig(
    format="\033[1;35m[downloader]\033[0m %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("downloader")

os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "180")


# Each entry: (repo_id, repo_filepath, local_subdir, friendly_name [, local_filename])
# - local_subdir is relative to <workspace>/models/  (may contain '/' for nested dirs)
# - local_filename, if present, renames the file at the destination
PRIMARY_FILES: list[tuple] = [
    # ---------- Flux 2 Dev (Comfy-Org pre-split, ComfyUI-native) ----------
    (
        "Comfy-Org/flux2-dev",
        "split_files/diffusion_models/flux2_dev_fp8mixed.safetensors",
        "diffusion_models",
        "Flux 2 Dev DiT (fp8 mixed, 35.5GB)",
    ),
    (
        "Comfy-Org/flux2-dev",
        "split_files/vae/flux2-vae.safetensors",
        "vae",
        "Flux 2 VAE",
    ),
    (
        "Comfy-Org/flux2-dev",
        "split_files/text_encoders/mistral_3_small_flux2_bf16.safetensors",
        "text_encoders",
        "Flux 2 Mistral-3 Small text encoder (BF16, 35.6GB — best quality)",
    ),
    (
        "Comfy-Org/flux2-dev",
        "split_files/text_encoders/mistral_3_small_flux2_fp4_mixed.safetensors",
        "text_encoders",
        "Flux 2 Mistral-3 Small text encoder (NVFP4 mixed, 12.3GB — sm_121a accelerated)",
    ),
    (
        "Comfy-Org/flux2-dev",
        "split_files/loras/Flux2TurboComfyv2.safetensors",
        "loras",
        "Flux 2 Turbo LoRA (fewer-step inference)",
    ),

    # ---------- LTX 2.3 — Kijai's ComfyUI-ready conversion of Lightricks/LTX-2.3 ----------
    (
        "Kijai/LTX2.3_comfy",
        "diffusion_models/ltx-2.3-22b-dev_transformer_only_bf16.safetensors",
        "diffusion_models",
        "LTX 2.3 22B Dev DiT (BF16, 42GB — full quality)",
    ),
    (
        "Kijai/LTX2.3_comfy",
        "diffusion_models/ltx-2.3-22b-dev_transformer_only_fp8_scaled.safetensors",
        "diffusion_models",
        "LTX 2.3 22B Dev DiT (FP8 scaled, 23.5GB — fast alt)",
    ),
    (
        "Kijai/LTX2.3_comfy",
        "text_encoders/ltx-2.3_text_projection_bf16.safetensors",
        "text_encoders",
        "LTX 2.3 text projection layer",
    ),
    (
        "Kijai/LTX2.3_comfy",
        "vae/LTX23_video_vae_bf16.safetensors",
        "vae",
        "LTX 2.3 video VAE (BF16)",
    ),
    (
        "Kijai/LTX2.3_comfy",
        "vae/LTX23_audio_vae_bf16.safetensors",
        "vae",
        "LTX 2.3 audio VAE (BF16)",
    ),
    (
        "Kijai/LTX2.3_comfy",
        "vae/taeltx2_3.safetensors",
        "vae",
        "LTX 2.3 tiny preview VAE",
    ),
    (
        "Kijai/LTX2.3_comfy",
        "loras/ltx-2.3-22b-distilled-1.1_lora-dynamic_fro09_avg_rank_111_bf16.safetensors",
        "loras",
        "LTX 2.3 distilled 1.1 dynamic LoRA (8-step)",
    ),

    # ---------- Gemma encoder for LTX-2.3 (Comfy-Org split) ----------
    (
        "Comfy-Org/ltx-2",
        "split_files/text_encoders/gemma_3_12B_it.safetensors",
        "text_encoders",
        "Gemma-3 12B IT text encoder (BF16, 24.4GB — best quality)",
    ),
    (
        "Comfy-Org/ltx-2",
        "split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors",
        "text_encoders",
        "Gemma-3 12B IT text encoder (NVFP4 mixed, 9.4GB — sm_121a accelerated)",
    ),

    # ---------- Abliterated LoRA for Gemma encoder (Comfy-Org/ltx-2) ----------
    (
        "Comfy-Org/ltx-2",
        "split_files/loras/gemma-3-12b-it-abliterated_heretic_lora_rank64_bf16.safetensors",
        "loras",
        "Gemma-3 abliterated 'heretic' LoRA (apply on top of Gemma encoder for LTX-2.3)",
    ),
    (
        "Comfy-Org/ltx-2",
        "split_files/loras/gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors",
        "loras",
        "Gemma-3 abliterated LoRA (alternate variant)",
    ),

    # ---------- Canonical-workflow extras (matches Lightricks + Comfy templates) ----------
    (
        "Lightricks/LTX-2.3-fp8",
        "ltx-2.3-22b-dev-fp8.safetensors",
        "checkpoints",
        "LTX 2.3 22B Dev FP8 full checkpoint (29GB — used by the canonical T2V/I2V templates)",
    ),
    (
        "Lightricks/LTX-2.3",
        "ltx-2.3-22b-distilled-lora-384.safetensors",
        "loras",
        "LTX 2.3 distilled LoRA-384 (canonical 8-step distilled LoRA, 7.6GB)",
    ),
    # VBVR Physics LoRA — required by movie_maker_fast.py fast/quality modes.
    # Place in ltx2/ subdirectory. ComfyUI registers as: ltx2/Ltx2.3-Licon-VBVR-I2V-96000-R32.safetensors
    # HuggingFace: https://huggingface.co/LiconStudio/Ltx2.3-VBVR-lora-I2V
    (
        "LiconStudio/Ltx2.3-VBVR-lora-I2V",
        "Ltx2.3-Licon-VBVR-I2V-96000-R32.safetensors",
        "loras/ltx2",
        "LTX 2.3 VBVR Physics LoRA (enhances motion dynamics and temporal consistency, 2.9GB)",
    ),
    # IC-LoRA Union Control — required by movie_maker_fast.py fast/quality modes.
    # Enables reference-based video-to-video control.
    # HuggingFace: https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control
    (
        "Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control",
        "ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors",
        "loras",
        "LTX 2.3 IC-LoRA Union Control (reference-based video-to-video control, 3.5GB)",
    ),
    (
        "Lightricks/LTX-2.3",
        "ltx-2.3-spatial-upscaler-x2-1.1.safetensors",
        "latent_upscale_models",
        "LTX 2.3 spatial upscaler x2 v1.1 (canonical 2-stage upscaling)",
    ),
    (
        "Lightricks/LTX-2.3",
        "ltx-2.3-temporal-upscaler-x2-1.0.safetensors",
        "latent_upscale_models",
        "LTX 2.3 temporal upscaler x2 v1.0 (motion smoothing)",
    ),
    (
        "black-forest-labs/FLUX.2-small-decoder",
        "full_encoder_small_decoder.safetensors",
        "vae",
        "Flux 2 full-encoder small-decoder VAE (used by canonical Flux 2 t2i template, 250MB)",
    ),
    (
        "ByteZSzn/Flux.2-Turbo-ComfyUI",
        "Flux_2-Turbo-LoRA_comfyui.safetensors",
        "loras",
        "Flux 2 Turbo LoRA (canonical filename — alternate to Flux2TurboComfyv2.safetensors)",
    ),

    # ---------- Files referenced by Lightricks's distilled workflows that the
    #            earlier download set missed (issue caught during workflow validation) ----------
    (
        "Lightricks/LTX-2.3",
        "ltx-2.3-22b-dev.safetensors",
        "checkpoints",
        "LTX 2.3 22B Dev BF16 full checkpoint (46GB — Lightricks single-stage distilled workflow)",
    ),
    (
        "Lightricks/LTX-2.3",
        "ltx-2.3-22b-distilled-lora-384-1.1.safetensors",
        "loras/ltxv/ltx2",
        "LTX 2.3 distilled LoRA-384 v1.1 (7.6GB — nested under loras/ltxv/ltx2/ as workflow expects)",
    ),
    (
        "Lightricks/LTX-2.3-fp8",
        "ltx-2.3-22b-distilled-fp8.safetensors",
        "checkpoints",
        "LTX 2.3 22B distilled FP8 checkpoint (29GB — flf2v workflow)",
    ),
    (
        "AviadDahan/LTX-2.3-ID-LoRA-TalkVid-3K",
        "lora_weights.safetensors",
        "loras",
        "LTX 2.3 ID LoRA TalkVid 3K (1.2GB — id_lora workflow)",
        "ltx-2.3-id-lora-talkvid-3k.safetensors",
    ),
    (
        "Comfy-Org/ltx-2",
        "split_files/text_encoders/gemma_3_12B_it.safetensors",
        "text_encoders",
        "Gemma-3 12B IT under the comfy_-prefixed name Lightricks's distilled workflow expects (BF16, 24.4GB)",
        "comfy_gemma_3_12B_it.safetensors",
    ),
    (
        "black-forest-labs/FLUX.2-klein-base-9b-fp8",
        "flux-2-klein-base-9b-fp8.safetensors",
        "diffusion_models",
        "Flux 2 Klein base 9B FP8 (9.5GB — Klein 9B workflow)",
    ),
    (
        "Comfy-Org/vae-text-encorder-for-flux-klein-9b",
        "split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors",
        "text_encoders",
        "Qwen 3 8B FP8 mixed text encoder for Flux 2 Klein 9B (8.7GB)",
    ),

    # ---------- LTX 2.3 distilled-1.1 fp8 (kijai/ComfyUI-PromptRelay workflow) ----------
    (
        "Kijai/LTX2.3_comfy",
        "diffusion_models/ltx-2.3-22b-distilled-1.1_transformer_only_fp8_scaled.safetensors",
        "diffusion_models",
        "LTX 2.3 22B distilled-1.1 transformer-only FP8 scaled (25GB — kijai PromptRelay workflow)",
    ),

    # ---------- ACE-Step v1.5 audio model (powers the Ancient_Sufi workflow) ----------
    (
        "Comfy-Org/ace_step_1.5_ComfyUI_files",
        "split_files/diffusion_models/acestep_v1.5_xl_turbo_bf16.safetensors",
        "diffusion_models",
        "ACE-Step v1.5 XL Turbo DiT (BF16, 9.97GB — Ancient_Sufi workflow)",
    ),
    (
        "Comfy-Org/ace_step_1.5_ComfyUI_files",
        "split_files/text_encoders/qwen_0.6b_ace15.safetensors",
        "text_encoders",
        "ACE-Step v1.5 Qwen 0.6B text encoder (CLIP-A, 1.19GB)",
    ),
    (
        "Comfy-Org/ace_step_1.5_ComfyUI_files",
        "split_files/text_encoders/qwen_4b_ace15.safetensors",
        "text_encoders",
        "ACE-Step v1.5 Qwen 4B text encoder (CLIP-B, 8.38GB)",
    ),
    (
        "Comfy-Org/ace_step_1.5_ComfyUI_files",
        "split_files/vae/ace_1.5_vae.safetensors",
        "vae",
        "ACE-Step v1.5 1D audio VAE (337MB)",
    ),
]

# Optional snapshot downloads — full HF-format abliterated LLM weights for
# users who want to swap in a fully-abliterated text encoder via custom nodes.
ABLITERATED_SNAPSHOTS: list[tuple[str, str, str, list[str]]] = [
    # (repo_id, local_subdir under text_encoders/, friendly_name, allow_patterns)
    (
        "huihui-ai/Huihui-Mistral-Small-3.2-24B-Instruct-2506-abliterated",
        "abliterated/Mistral-Small-3.2-24B-abliterated",
        "Huihui Mistral-Small-3.2 24B abliterated (full HF weights — swap-in alt for Flux 2)",
        ["*.safetensors", "*.json", "*.model", "tokenizer*", "config*"],
    ),
    (
        "huihui-ai/gemma-3-12b-it-abliterated",
        "abliterated/Gemma-3-12B-IT-abliterated",
        "Huihui Gemma-3 12B IT abliterated (full HF weights — swap-in alt for LTX 2.3)",
        ["*.safetensors", "*.json", "*.model", "tokenizer*", "config*"],
    ),
]


def _retry(callable_, *, attempts: int = 4, base_delay: float = 5.0):
    last = None
    for i in range(attempts):
        try:
            return callable_()
        except (HfHubHTTPError, ConnectionError, OSError) as e:
            last = e
            wait = base_delay * (2 ** i)
            log.warning("attempt %d/%d failed (%s); retrying in %.0fs", i + 1, attempts, e, wait)
            time.sleep(wait)
    raise last  # type: ignore[misc]


def fetch_file(repo_id: str, repo_path: str, dst_dir: Path, friendly: str,
               token: str | None, local_filename: str | None = None) -> bool:
    """Download a single file from HF.

    Args:
        repo_id, repo_path: where the file lives on HF
        dst_dir: target directory (already includes nested subdirs from the entry's local_subdir)
        friendly: human label for logs
        local_filename: if provided, the file is saved under this name (renames the HF basename)
    """
    target_name = local_filename or Path(repo_path).name
    final_path = dst_dir / target_name
    if final_path.exists() and final_path.stat().st_size > 0:
        log.info("✓ already present: %s", friendly)
        return True

    log.info("⤓ %s  (%s :: %s%s)", friendly, repo_id, repo_path,
             f"  → renamed to {target_name}" if local_filename else "")
    dst_dir.mkdir(parents=True, exist_ok=True)
    try:
        out = _retry(lambda: hf_hub_download(
            repo_id=repo_id,
            filename=repo_path,
            local_dir=str(dst_dir),
            token=token,
        ))
        out_path = Path(out)
        # Flatten any HF-imposed subfolder (split_files/...) and apply rename
        if out_path != final_path and out_path.exists():
            final_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                out_path.replace(final_path)
            except OSError:
                import shutil
                shutil.copy2(out_path, final_path)
                out_path.unlink(missing_ok=True)
            # Clean empty parent dirs left behind
            try:
                parent = out_path.parent
                while parent != dst_dir and not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
            except OSError:
                pass
        log.info("✓ done: %s -> %s", friendly, final_path)
        return True
    except Exception as e:
        log.error("✗ failed: %s (%s)", friendly, e)
        return False


def fetch_snapshot(repo_id: str, dst_dir: Path, friendly: str, allow: Iterable[str], token: str | None) -> bool:
    if dst_dir.exists() and any(dst_dir.glob("*.safetensors")):
        log.info("✓ snapshot already present: %s", friendly)
        return True
    log.info("⤓ snapshot %s  (%s)", friendly, repo_id)
    dst_dir.mkdir(parents=True, exist_ok=True)
    try:
        _retry(lambda: snapshot_download(
            repo_id=repo_id,
            local_dir=str(dst_dir),
            allow_patterns=list(allow),
            token=token,
        ))
        log.info("✓ done snapshot: %s -> %s", friendly, dst_dir)
        return True
    except Exception as e:
        log.error("✗ snapshot failed: %s (%s)", friendly, e)
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, help="Persistent workspace root (parent of models/)")
    parser.add_argument("--skip-abliterated", action="store_true", help="Skip downloading full abliterated LLM snapshots")
    args = parser.parse_args()

    ws = Path(args.workspace)
    models = ws / "models"
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token:
        log.info("HF token detected — gated repos accessible")
    else:
        log.warning("no HF_TOKEN set — gated repos (e.g. FLUX.2-dev source) may be inaccessible")

    successes = 0
    failures = 0

    # 1. Primary file-by-file downloads
    for entry in PRIMARY_FILES:
        # Backwards compatible: 4-tuple (canonical) or 5-tuple (with rename)
        if len(entry) == 5:
            repo_id, repo_path, subdir, friendly, local_filename = entry
        else:
            repo_id, repo_path, subdir, friendly = entry
            local_filename = None
        ok = fetch_file(repo_id, repo_path, models / subdir, friendly, token, local_filename)
        successes += int(ok)
        failures += int(not ok)

    # 2. Optional abliterated snapshots
    if not args.skip_abliterated and os.environ.get("SKIP_ABLITERATED", "0") != "1":
        for repo_id, subdir, friendly, allow in ABLITERATED_SNAPSHOTS:
            ok = fetch_snapshot(repo_id, models / "text_encoders" / subdir, friendly, allow, token)
            successes += int(ok)
            failures += int(not ok)

    log.info("=" * 60)
    log.info("download summary: %d ok, %d failed", successes, failures)
    log.info("=" * 60)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
