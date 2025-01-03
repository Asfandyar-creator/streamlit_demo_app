import gradio as gr
import os

def process_message(message, file, history):
    if file is not None:
        # Process uploaded file
        file_msg = f"Received file: {file.name}"
        history.append(("You", f"{message}\nUploaded file: {file.name}"))
        history.append(("Bot", file_msg))
    else:
        # Process text message only
        history.append(("You", message))
        history.append(("Bot", f"You said: {message}"))
    
    return history, ""  # Return history and clear input

def clear_chat():
    return [], ""  # Return empty history and input

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    with gr.Row():
        # Sidebar using Column
        with gr.Column(scale=1, min_width=100):
            clear = gr.Button("Clear Chat")
            
        # Main chat area
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                [],
                elem_id="chatbox",
                bubble_full_width=False,
                avatar_images=("👤", "🤖"),
                height=600,
                type="messages"  # Added to address the deprecation warning
            )
            
            with gr.Row():
                with gr.Column(scale=8):
                    txt = gr.Textbox(
                        show_label=False,
                        placeholder="Type your message here...",
                        container=False
                    )
                with gr.Column(scale=1):
                    file_upload = gr.File(
                        file_count="single",
                        file_types=["image", "video", "audio", "text"],
                        show_label=False
                    )
                with gr.Column(scale=1):
                    submit_btn = gr.Button("Submit", variant="primary")

    # Set up event handlers
    submit_btn.click(
        process_message,
        inputs=[txt, file_upload, chatbot],
        outputs=[chatbot, txt]
    )
    txt.submit(
        process_message,
        inputs=[txt, file_upload, chatbot],
        outputs=[chatbot, txt]
    )
    clear.click(
        clear_chat,
        outputs=[chatbot, txt]
    )

if __name__ == "__main__":
    demo.launch()