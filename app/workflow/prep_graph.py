from langgraph.graph import END, StateGraph

from app.workflow.nodes import (
    
    load_document_and_history, 
    retrieve_selected_section_chunks,
     generate_questions,
     simulate_and_score_answers, 
    persist_session, 
    
     
)
from app.workflow.state import PrepWorkflowState


def build_prep_graph():
    graph = StateGraph(PrepWorkflowState)

    graph.add_node("load_document_and_history", load_document_and_history)
    graph.add_node("retrieve_selected_section_chunks", retrieve_selected_section_chunks)
    graph.add_node("generate_questions", generate_questions)
    graph.add_node("simulate_and_score_answers", simulate_and_score_answers)
    graph.add_node("persist_session", persist_session)

    graph.set_entry_point("load_document_and_history")
    graph.add_edge("load_document_and_history", "retrieve_selected_section_chunks")
    graph.add_edge("retrieve_selected_section_chunks", "generate_questions")
    graph.add_edge("generate_questions", "simulate_and_score_answers")
    graph.add_edge("simulate_and_score_answers", "persist_session")
    graph.add_edge("persist_session", END)

    return graph.compile()


prep_graph = build_prep_graph()