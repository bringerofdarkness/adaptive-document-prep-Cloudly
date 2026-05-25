import time
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8090"

st.set_page_config(
    page_title="Adaptive Study Assistant",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 Adaptive Study Assistant")
st.caption("Personalized Mock Exam Platform powered by Historical Performance Analytics")
st.markdown("---")

if "session_active" not in st.session_state:
    st.session_state.session_active = False
if "current_questions" not in st.session_state:
    st.session_state.current_questions = []
if "task_id" not in st.session_state:
    st.session_state.task_id = None
if "target_sections" not in st.session_state:
    st.session_state.target_sections = ""
if "backend_session_id" not in st.session_state:
    st.session_state.backend_session_id = None
if "evaluation_data" not in st.session_state:
    st.session_state.evaluation_data = None

if not st.session_state.session_active:
    st.header("🎯 Prepare Your Practice Session")
    
    section_inputs = st.text_input(
        "Enter Chapter or Section IDs (Comma-separated)", 
        placeholder="e.g., 1, 2", 
        value=st.session_state.target_sections
    )
    
    num_questions = st.number_input(
        "Number of Questions per Section", 
        min_value=1, 
        max_value=20, 
        value=5, 
        step=1
    )

    if st.button("Generate My Practice Exam", type="primary"):
        if not section_inputs.strip():
            st.warning("Please specify at least one Chapter or Section ID to proceed.")
        else:
            st.session_state.target_sections = section_inputs
            try:
                parsed_sections = [int(s.strip()) for s in section_inputs.split(",") if s.strip()]
            except ValueError:
                st.error("Please ensure all IDs are entered as valid numbers.")
                st.stop()
            
            payload = {
                "selected_section_numbers": parsed_sections,
                "questions_per_section": int(num_questions)
            }
            
            status_box = st.empty()
            progress_bar = st.progress(0)
            status_box.info("🔍 Analyzing study materials and syncing with your personal learning history...")
            
            try:
                res = requests.post(f"{BACKEND_URL}/prep/start", json=payload)
                
                if res.status_code in [200, 202]:
                    st.session_state.task_id = res.json().get("task_id")
                    
                    polls = 0
                    is_complete = False
                    while not is_complete and polls < 60:
                        time.sleep(1)
                        polls += 1
                        
                        status_res = requests.get(f"{BACKEND_URL}/prep/task/{st.session_state.task_id}")
                        if status_res.status_code == 200:
                            state_matrix = status_res.json()
                            current_state = state_matrix.get("status")
                            
                            if current_state == "SUCCESS":
                                progress_bar.progress(100)
                                status_box.empty()
                                
                                result_payload = state_matrix.get("result", {})
                                st.session_state.current_questions = result_payload.get("questions", [])
                                st.session_state.backend_session_id = result_payload.get("session_id")
                                st.session_state.evaluation_data = None
                                st.session_state.session_active = True
                                is_complete = True
                                st.rerun()
                            elif current_state == "FAILURE":
                                status_box.error("An error occurred while generating questions. Please try resetting the engine.")
                                is_complete = True
                            else:
                                progress_bar.progress(min((polls / 60), 0.95))
                                status_box.info("🤖 AI is customizing questions based on your strengths and weaknesses...")
                        else:
                            status_box.error("Connection lost with the evaluation engine.")
                            is_complete = True
                else:
                    st.error("Failed to initialize session. Please verify database connectivity.")
            except Exception as e:
                st.error(f"Network processing error: {str(e)}")

else:
    if st.session_state.evaluation_data is None:
        st.header("📝 Live Practice Exam")
        st.info(f"📋 Focus Chapters: [ {st.session_state.target_sections} ]")
        
        user_responses = {}
        
        for idx, q in enumerate(st.session_state.current_questions):
            st.markdown(f"### Q{idx + 1}. {q.get('question')}")
            st.caption(f"Location: Section {q.get('section_number')} | Topic: {q.get('topic')} | Difficulty: {str(q.get('difficulty')).capitalize()}")
            
            options_dict = q.get("options", {})
            options_list = list(options_dict.values())
            
            selected_value = st.radio(
                f"Choose your answer for Q{idx + 1}:",
                options=options_list,
                key=f"q_radio_{q.get('question_id')}"
            )
            
            selected_key = "A"
            for k, v in options_dict.items():
                if v == selected_value:
                    selected_key = k
                    break
                    
            user_responses[str(q.get("question_id"))] = str(selected_key)
            st.markdown("<br>", unsafe_allow_html=True)
            
        st.markdown("---")
        
        if st.button("Submit My Answers", type="primary"):
            try:
                submit_payload = {
                    "session_id": st.session_state.backend_session_id,
                    "answers": user_responses
                }
                
                submit_res = requests.post(f"{BACKEND_URL}/prep/submit", json=submit_payload)
                
                if submit_res.status_code in [200, 201]:
                    st.session_state.evaluation_data = submit_res.json()
                    st.rerun()
                else:
                    st.error("Submission failed. Please check backend integration states.")
            except Exception as e:
                st.error(f"Network error during answer verification: {str(e)}")
    else:
        st.header("🏁 Exam Performance Report")
        st.success("Your practice exam has been evaluated and logged successfully!")
        
        eval_data = st.session_state.evaluation_data
        
        correct = int(eval_data.get("correct_count", 0))
        total = int(eval_data.get("total_questions", 0))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Your Score", f"{correct} / {total}")
        with col2:
            st.metric("Personalization Engine", "ACTIVE")
            
        st.info("💡 **Learning Progress Updated:** Your strengths and weaknesses have been updated in your profile database.")
        
        st.markdown("### 🔍 Question Review & Explanations")
        for idx, report in enumerate(eval_data.get("results", [])):
            is_correct = report.get("is_correct")
            q_text = st.session_state.current_questions[idx].get("question")
            reason = st.session_state.current_questions[idx].get("adaptation_reason")
            
            if is_correct:
                st.success(f"**Q{idx + 1}. Correct** — {q_text}")
                st.markdown(f"- **Your Answer:** `{report.get('selected_answer')}`")
            else:
                st.error(f"**Q{idx + 1}. Incorrect** — {q_text}")
                st.markdown(f"- **Your Answer:** `{report.get('selected_answer')}` | **Correct Answer:** `{report.get('correct_answer')}`")
                st.markdown(f"- **📖 Rationale:** *{report.get('clarification')}*")
            
            st.caption(f"🧠 **AI Customization Logic:** {reason}")
            st.markdown("---")
        
        st.subheader("📋 System Knowledge Base Snapshot")
        st.markdown("Your historical performance metrics have been compiled for evaluator verification.")
        
        with st.container(border=True):
            st.markdown(f"**🔬 Session Identifier Token:** `{eval_data.get('session_id')}`")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"📂 **Chapters Covered:** \n`Section {st.session_state.target_sections}`")
            with c2:
                st.markdown(f"🎯 **Session Accuracy:** \n`Score: {eval_data.get('score', 0)}%`")
            with c3:
                st.markdown(f"📊 **Answer Distribution:** \n`Correct: {eval_data.get('correct_count', 0)}` | `Wrong: {eval_data.get('wrong_count', 0)}`")
        
        with st.expander("🛠️ View Technical Telemetry Data for Evaluator Audit"):
            st.json({
                "session_id": eval_data.get("session_id"),
                "score_percentage": eval_data.get("score"),
                "correct_count": eval_data.get("correct_count"),
                "wrong_count": eval_data.get("wrong_count"),
                "total_questions": eval_data.get("total_questions"),
                "target_focus_sections": st.session_state.target_sections
            })
        
        if st.button("Start Another Practice Exam", type="primary"):
            st.session_state.session_active = False
            st.session_state.current_questions = []
            st.session_state.task_id = None
            st.session_state.backend_session_id = None
            st.session_state.evaluation_data = None
            st.rerun()