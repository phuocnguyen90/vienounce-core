import os
import sys
import time
import gradio as gr

# Setup path resolution
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Initialize local offline model container from the core package
print("Initializing offline model container...")
from vienounce_core.models import local_models
local_models.initialize()

from vienounce_core.diagnostics import DiagnosticsService

# Instantiate DiagnosticsService locally with local models
diag_service = DiagnosticsService(
    phoneme_model=local_models.phoneme_model,
    feature_extractor=local_models.feature_extractor,
    vocab=local_models.vocab,
    g2p_pipeline=local_models.g2p_pipeline
)

def render_highlights_to_html(words_data) -> str:
    html_blocks = []
    for word_info in words_data:
        word = word_info["word"]
        skipped = word_info.get("skipped", False)
        
        # Word text styling
        if skipped:
            word_style = "color: #64748b; font-weight: bold; text-decoration: line-through; font-size: 24px; font-family: sans-serif;"
        else:
            word_style = "color: #f1f5f9; font-weight: bold; font-size: 24px; font-family: sans-serif;"
            
        # Compile phoneme badges HTML
        phone_badges = []
        for h in word_info["highlights"]:
            phone = h["phone"]
            status = "gray" if skipped else h["status"]
            
            if status == "green":
                bg = "#064e3b"
                fg = "#10b981"
                border = "#047857"
            elif status == "yellow":
                bg = "#78350f"
                fg = "#fbbf24"
                border = "#b45309"
            elif status == "red":
                bg = "#7f1d1d"
                fg = "#f87171"
                border = "#b91c1c"
            else:
                bg = "#1e293b"
                fg = "#94a3b8"
                border = "#334155"
                
            badge_html = f'<span style="background-color: {bg}; color: {fg}; border: 1px solid {border}; border-radius: 6px; padding: 4px 8px; font-family: monospace; font-size: 14px; font-weight: 600;">/{phone}/</span>'
            phone_badges.append(badge_html)
            
        badges_row_html = f'<div style="display: flex; gap: 4px; justify-content: center; margin-top: 8px; flex-wrap: wrap;">{"".join(phone_badges)}</div>'
        
        block_html = f"""
        <div style="display: flex; flex-direction: column; align-items: center; min-width: 80px; padding: 10px; background-color: #0f172a; border-radius: 8px; border: 1px solid #1e293b;">
            <span style="{word_style}">{word}</span>
            {badges_row_html}
        </div>
        """
        html_blocks.append(block_html)
        
    return """
    <div style="background-color: #020617; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #1e293b; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); margin-top: 15px;">
        <p style="margin: 0 0 16px 0; color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Diagnostic Accent Highlights</p>
        <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 14px;">
            {body}
        </div>
        <div style="display: flex; justify-content: center; gap: 24px; margin-top: 24px; font-size: 13px; color: #94a3b8; font-weight: 500;">
            <span><span style="display: inline-block; width: 10px; height: 10px; background-color: #064e3b; border: 1px solid #047857; border-radius: 3px; margin-right: 6px;"></span>Correct (GOP &ge; -2.5)</span>
            <span><span style="display: inline-block; width: 10px; height: 10px; background-color: #78350f; border: 1px solid #b45309; border-radius: 3px; margin-right: 6px;"></span>Accented (&ge; -5.0)</span>
            <span><span style="display: inline-block; width: 10px; height: 10px; background-color: #7f1d1d; border: 1px solid #b91c1c; border-radius: 3px; margin-right: 6px;"></span>Error (< -5.0)</span>
        </div>
    </div>
    """.format(body=" ".join(html_blocks))

def handle_diagnose(audio_path: str, target_text: str):
    if not audio_path:
        return "⚠️ Please record your speech or upload a WAV file.", ""
    if not target_text.strip():
        return "⚠️ Please enter the target sentence first.", ""
        
    try:
        # Run diagnostics locally in-memory
        res_data = diag_service.diagnose_audio(audio_path, target_text)
        score = res_data["overall_score"]
        
        # Format metric card
        score_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 60 else "#ef4444")
        score_card = f"""
        <div style="text-align: center; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; padding: 20px; border: 1px solid #334155;">
            <p style="margin: 0; color: #94a3b8; font-size: 14px; font-weight: bold; text-transform: uppercase;">Overall Pronunciation Score</p>
            <p style="margin: 8px 0 0 0; font-size: 48px; font-weight: 800; color: {score_color};">{score}%</p>
        </div>
        """
        
        highlights_html = render_highlights_to_html(res_data["words"])
        return score_card, highlights_html
        
    except Exception as e:
        return f"❌ Diagnostics Error: {str(e)}", ""

# =====================================================================
# GRADIO INTERFACE LAYOUT (Local & Offline Core Demonstration)
# =====================================================================
with gr.Blocks(theme=gr.themes.Soft(primary_hue="emerald", secondary_hue="indigo")) as demo:
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #10b981; font-weight: 800; font-size: 36px; margin: 0;">Vienounce Core</h1>
        <p style="color: #94a3b8; font-size: 16px; margin-top: 4px;">Open-Source Phone-Level English Pronunciation Diagnostics</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.HTML("<h3 style='color: #10b981; margin: 0;'>1. Enter Practice Sentence</h3>")
            practice_text = gr.Textbox(
                value="I like to eat apples",
                label="Target English Sentence",
                placeholder="Type an English phrase to practice..."
            )
            
            gr.HTML("<div style='margin-top: 20px;'><h3 style='color: #10b981; margin: 0;'>2. Record Attempt</h3></div>")
            user_audio = gr.Audio(
                label="Your Speech (Microphone / WAV)",
                type="filepath",
                sources=["microphone", "upload"]
            )
            btn_diagnose = gr.Button("Diagnose My Pronunciation", variant="primary")
            
        with gr.Column(scale=1):
            gr.HTML("<h3 style='color: #10b981; margin: 0;'>3. Diagnostic Feedback</h3>")
            diagnostic_score = gr.HTML(value="")
            diagnostic_highlights = gr.HTML(value="")
            
    # Connect actions
    btn_diagnose.click(
        fn=handle_diagnose,
        inputs=[user_audio, practice_text],
        outputs=[diagnostic_score, diagnostic_highlights]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
