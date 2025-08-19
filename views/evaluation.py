import streamlit as st
import json
import os
import plotly.graph_objects as go

def show_evaluation_page():
    # Evaluation pipeline diagram (dark theme friendly)
    st.markdown("### Evaluation pipeline")
    fig_pipe = go.Figure()
    steps = [
        "Synthetic test set",
        "LLM critic",
        "Ask question to RAG",
        "Judge RAG response",
        "Calculate accuracy"
    ]
    box_color = "#23272f"  # dark box
    border_color = "#4f8cff"  # blue border
    text_color = "#e5e7eb"  # light text
    arrow_color = "#4f8cff"
    for i, step in enumerate(steps):
        fig_pipe.add_shape(
            type="rect",
            x0=i*2, x1=i*2+1.5, y0=0, y1=1,
            line=dict(color=border_color, width=2), fillcolor=box_color, layer="below"
        )
        fig_pipe.add_annotation(
            x=i*2+0.75, y=0.5, text=step, showarrow=False, font=dict(size=14, color=text_color),
            xanchor="center", yanchor="middle"
        )
        if i < len(steps)-1:
            fig_pipe.add_annotation(
                x=i*2+1.6, y=0.5, text="→", showarrow=False, font=dict(size=24, color=arrow_color),
                xanchor="left", yanchor="middle"
            )
    fig_pipe.update_xaxes(visible=False, range=[-0.5, len(steps)*2-0.5])
    fig_pipe.update_yaxes(visible=False, range=[-0.2, 1.2])
    fig_pipe.update_layout(
        height=160, margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="#181c22", paper_bgcolor="#181c22"
    )
    st.plotly_chart(fig_pipe, use_container_width=True)
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>Evaluation Results</h1>
        <p style="color: #666; font-size: 1.1rem;">
            Automated evaluation of RAG, LLM-only, and RAG-CoT methods
        </p>
    </div>
    """, unsafe_allow_html=True)

    eval_dir = os.path.join(os.path.dirname(__file__), '../evals')
    rag_metrics_path = os.path.join(eval_dir, 'rag_metrics.json')
    llm_metrics_path = os.path.join(eval_dir, 'llm_metrics.json')
    rag_cot_metrics_path = os.path.join(eval_dir, 'rag_cot_metrics.json')

    # Load metrics
    with open(rag_metrics_path) as f:
        rag_metrics = json.load(f)
    with open(llm_metrics_path) as f:
        llm_metrics = json.load(f)
    with open(rag_cot_metrics_path) as f:
        rag_cot_metrics = json.load(f)

    # Prepare data for plot
    labels = ["accuracy"]
    methods = ["llm-only", "rag", "rag-cot"]
    metric_matrix = [
        [llm_metrics[k] for k in labels],
        [rag_metrics[k] for k in labels],
        [rag_cot_metrics[k] for k in labels]
    ]

    unknown_vals = [
        llm_metrics["unknown_count"] / llm_metrics["total_count"],
        rag_metrics["unknown_count"] / rag_metrics["total_count"],
        rag_cot_metrics["unknown_count"] / rag_cot_metrics["total_count"]
    ]

    # Plotly chart
    fig = go.Figure()
    # Accuracy line
    fig.add_trace(go.Scatter(
        x=methods,
        y=[metric_matrix[0][0], metric_matrix[1][0], metric_matrix[2][0]],
        mode="lines+markers+text",
        name="accuracy (↑ better)",
        text=[f"{v:.1%}" for v in [metric_matrix[0][0], metric_matrix[1][0], metric_matrix[2][0]]],
        textposition="top center"
    ))
    # Unknown line
    fig.add_trace(go.Scatter(
        x=methods,
        y=unknown_vals,
        mode="lines+markers+text",
        name="unknown (↓ better)",
        line=dict(dash="dash", color="orange"),
        marker=dict(symbol="square", color="orange"),
        text=[f"{v:.1%}" for v in unknown_vals],
        textposition="top center"
    ))
    fig.update_layout(
        yaxis=dict(range=[0, 1.1], title="ratio (%)"),
        xaxis=dict(title="methods"),
        title=f"Evaluation on {rag_metrics['total_count']} questions | judge llm: azure gpt-4o",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        height=400,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Show metrics as table
    st.markdown("### Metrics summary")
    metrics_table = [
        {"Method": "LLM-only", **llm_metrics},
        {"Method": "RAG", **rag_metrics},
        {"Method": "RAG-CoT", **rag_cot_metrics},
    ]
    import pandas as pd

    excluded_columns = ['answerable_accuracy', 'coverage']
    metrics_df = pd.DataFrame(metrics_table).drop(columns=excluded_columns)
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    # Show some evaluated questions and answers
    st.markdown("### Sample evaluated questions and answers")
    qa_list_path = os.path.join(eval_dir, 'qa_list.json')
    rag_answers_path = os.path.join(eval_dir, 'qa_list_results.json')
    with open(qa_list_path) as f:
        qa_list = json.load(f)
    with open(rag_answers_path) as f:
        rag_answers = json.load(f)

    # Show a few samples
    for i, (qa, ans) in enumerate(zip(qa_list[:5], rag_answers[:5])):
        with st.expander(f"Q{i+1}: {qa['question'][:80]}{'...' if len(qa['question'])>80 else ''}"):
            st.markdown("**Question:**")
            st.json(qa)
            st.markdown("**RAG Answer Evaluation:**")
            st.json(ans)