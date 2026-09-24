"""
Smart English Writing Assistant
Grammar Error Correction · Grammar Q&A · Interactive Quiz Learning

A SINGLE-FILE Streamlit app. No API keys required anywhere.

Run with:
    pip install -r requirements.txt
    streamlit run app.py
"""

import re
import time
import random
import functools
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd
import streamlit as st

try:
    import language_tool_python
except ImportError:
    language_tool_python = None


# ==========================================================================
# SECTION 1: GRAMMAR KNOWLEDGE BASE (for Grammar Q&A)
# ==========================================================================

@dataclass
class GrammarTopic:
    id: str
    title: str
    keywords: List[str]
    explanation: str
    rule: str
    example_wrong: str
    example_right: str
    lt_rule_hints: List[str] = field(default_factory=list)


KNOWLEDGE_BASE: List[GrammarTopic] = [
    GrammarTopic(
        id="subject_verb_agreement",
        title="Subject-Verb Agreement (he/she/it + verb-s)",
        keywords=["goes", "she go", "he go", "it go", "plays", "play cricket", "third person",
                   "singular", "agreement", "verb agreement", "he she it", "subject verb"],
        explanation=(
            "In the simple present tense, the verb must agree with its subject. "
            "With third-person singular subjects (he, she, it, or a singular noun), "
            "add -s or -es to the base verb. With I, you, we, they, or plural nouns, "
            "use the base form of the verb."
        ),
        rule="Singular third-person subject → verb + s/es. Plural/1st/2nd person subject → base verb.",
        example_wrong="She go to college.",
        example_right="She goes to college.",
        lt_rule_hints=["AGREEMENT", "SUBJECT_VERB", "HE_VERB_AGR", "PLURAL_VERB_AGREEMENT"],
    ),
    GrammarTopic(
        id="has_vs_have",
        title="Has vs Have",
        keywords=["has instead of have", "has", "have", "difference between has and have",
                   "why has", "instead of have"],
        explanation=(
            "'Has' and 'have' both come from the verb 'to have', used to show possession "
            "or form the present perfect tense. Use 'has' with he, she, it, and singular nouns. "
            "Use 'have' with I, you, we, they, and plural nouns."
        ),
        rule="he/she/it/singular noun → has. I/you/we/they/plural noun → have.",
        example_wrong="He have a car.",
        example_right="He has a car.",
        lt_rule_hints=["HAS_HAVE", "AGREEMENT"],
    ),
    GrammarTopic(
        id="is_are_am",
        title="Is vs Are vs Am",
        keywords=["is", "are", "am", "difference between is and are", "to be"],
        explanation=(
            "'Am', 'is', and 'are' are all forms of the verb 'to be' in the present tense. "
            "Use 'am' only with I. Use 'is' with he, she, it, and singular nouns. "
            "Use 'are' with you, we, they, and plural nouns."
        ),
        rule="I → am. he/she/it/singular → is. you/we/they/plural → are.",
        example_wrong="They is happy.",
        example_right="They are happy.",
        lt_rule_hints=["BE_VBG", "AGREEMENT"],
    ),
    GrammarTopic(
        id="was_vs_were",
        title="Was vs Were",
        keywords=["was", "were", "difference between was and were", "past tense to be"],
        explanation=(
            "'Was' and 'were' are the past-tense forms of 'to be'. Use 'was' with I, he, she, it, "
            "and singular nouns. Use 'were' with you, we, they, and plural nouns."
        ),
        rule="I/he/she/it/singular → was. you/we/they/plural → were.",
        example_wrong="They was late.",
        example_right="They were late.",
        lt_rule_hints=["AGREEMENT"],
    ),
    GrammarTopic(
        id="present_continuous",
        title="Present Continuous (be + verb-ing)",
        keywords=["am go", "is go", "am going", "continuous", "verb-ing", "-ing form", "i am go to school"],
        explanation=(
            "The present continuous tense describes actions happening right now, and it needs "
            "'to be' (am/is/are) followed by the verb in its -ing form. 'I am go' is incorrect "
            "because 'go' is missing the -ing ending."
        ),
        rule="Subject + am/is/are + verb-ing.",
        example_wrong="I am go to school.",
        example_right="I am going to school.",
        lt_rule_hints=["MISSING_VERB", "PROGRESSIVE_VERB_FORM"],
    ),
    GrammarTopic(
        id="simple_past",
        title="Simple Past Tense",
        keywords=["past tense", "yesterday", "ed ending", "irregular verb", "went", "goed"],
        explanation=(
            "The simple past describes a completed action. Regular verbs add -ed (played, "
            "walked), while irregular verbs change form entirely (go → went, eat → ate). "
            "There is no separate form for different subjects in the simple past."
        ),
        rule="Regular verb + ed. Irregular verbs must be memorised (go → went).",
        example_wrong="Yesterday I goed to the market.",
        example_right="Yesterday I went to the market.",
        lt_rule_hints=["MORFOLOGIK_RULE", "IRREGULAR_VERB"],
    ),
    GrammarTopic(
        id="articles",
        title="Articles: A, An, The",
        keywords=["a", "an", "the", "article", "when to use", "a or an",
                   "definite article", "indefinite article"],
        explanation=(
            "'A' and 'an' are indefinite articles used before a noun that is not specific or "
            "mentioned for the first time. Use 'a' before a consonant SOUND (a book, a university) "
            "and 'an' before a vowel SOUND (an apple, an hour). 'The' is the definite article, used "
            "when the noun is specific or already known to the listener (the sun, the book I bought)."
        ),
        rule="Consonant sound → a. Vowel sound → an. Specific/known noun → the.",
        example_wrong="I saw a elephant near the river.",
        example_right="I saw an elephant near the river.",
        lt_rule_hints=["EN_A_VS_AN", "ARTICLE"],
    ),
    GrammarTopic(
        id="prepositions",
        title="Prepositions (in, on, at)",
        keywords=["preposition", "in on at", "in vs on", "at vs in", "on vs at"],
        explanation=(
            "Prepositions of time and place follow general patterns: use 'at' for precise times "
            "and points (at 5 PM, at the door), 'on' for days and dates and surfaces (on Monday, "
            "on the table), and 'in' for longer periods and enclosed spaces (in June, in the box)."
        ),
        rule="Precise point → at. Days/dates/surfaces → on. Longer periods/enclosed spaces → in.",
        example_wrong="I will meet you in 5 PM.",
        example_right="I will meet you at 5 PM.",
        lt_rule_hints=["PREPOSITION"],
    ),
    GrammarTopic(
        id="double_negative",
        title="Double Negatives",
        keywords=["double negative", "don't have no", "not never"],
        explanation=(
            "Standard English avoids using two negative words in the same clause, because they "
            "can cancel each other out or sound non-standard. Use only one negative word to "
            "express a negative idea."
        ),
        rule="Use only one negative marker per clause.",
        example_wrong="I don't have no money.",
        example_right="I don't have any money.",
        lt_rule_hints=["DOUBLE_NEGATIVE"],
    ),
    GrammarTopic(
        id="its_vs_its_apostrophe",
        title="Its vs It's",
        keywords=["its vs it's", "apostrophe its", "it's or its"],
        explanation=(
            "'It's' is a contraction of 'it is' or 'it has'. 'Its' (no apostrophe) is a possessive "
            "pronoun meaning 'belonging to it'. A quick test: if you can expand it to 'it is' and "
            "the sentence still makes sense, use 'it's'."
        ),
        rule="it's = it is / it has. its = possession (no apostrophe).",
        example_wrong="The dog wagged it's tail.",
        example_right="The dog wagged its tail.",
        lt_rule_hints=["ITS_IT_S", "APOSTROPHE"],
    ),
    GrammarTopic(
        id="your_vs_youre",
        title="Your vs You're",
        keywords=["your vs you're", "you're or your"],
        explanation=(
            "'You're' is a contraction of 'you are'. 'Your' is a possessive pronoun meaning "
            "'belonging to you'. Try expanding to 'you are' to check which one fits."
        ),
        rule="you're = you are. your = possession.",
        example_wrong="Your welcome!",
        example_right="You're welcome!",
        lt_rule_hints=["YOUR_YOU_RE"],
    ),
    GrammarTopic(
        id="comparatives",
        title="Comparatives and Superlatives",
        keywords=["comparative", "superlative", "more good", "gooder", "-er -est"],
        explanation=(
            "Short adjectives (1-2 syllables) usually add -er/-est (tall → taller → tallest). "
            "Longer adjectives use more/most instead (beautiful → more beautiful → most beautiful). "
            "Some adjectives are irregular (good → better → best)."
        ),
        rule="Short adjective + er/est. Long adjective → more/most + adjective. Some are irregular.",
        example_wrong="This book is more good than that one.",
        example_right="This book is better than that one.",
        lt_rule_hints=["COMPARISON", "MORE_GOOD"],
    ),
]

_LT_HINT_INDEX = {}
for _topic in KNOWLEDGE_BASE:
    for _hint in _topic.lt_rule_hints:
        _LT_HINT_INDEX[_hint.upper()] = _topic.id


def _score_topic(question: str, topic: GrammarTopic) -> int:
    q = question.lower()
    q = re.sub(r"[^a-z0-9'\s]", " ", q)
    words = set(q.split())
    score = 0
    for kw in topic.keywords:
        kw = kw.lower()
        if " " in kw:
            if kw in q:
                score += len(kw.split())
        else:
            if kw in words:
                score += 2 if len(kw) > 3 else 1
    return score


def answer_question(question: str) -> dict:
    """Match a free-text grammar question to the best knowledge-base topic."""
    if not question or not question.strip():
        return {
            "matched": False,
            "answer": "Please type a grammar question, e.g. \"Why do we use 'has' instead of 'have'?\"",
            "topic": None,
        }

    scored = [(_score_topic(question, t), t) for t in KNOWLEDGE_BASE]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_topic = scored[0]

    if best_score == 0:
        suggestions = ", ".join(t.title for t in KNOWLEDGE_BASE[:5])
        return {
            "matched": False,
            "answer": (
                "I don't have a specific rule for that exact question yet, but here are some "
                f"related grammar topics you can ask about: {suggestions}."
            ),
            "topic": None,
        }

    return {
        "matched": True,
        "answer": best_topic.explanation,
        "rule": best_topic.rule,
        "example_wrong": best_topic.example_wrong,
        "example_right": best_topic.example_right,
        "topic": best_topic,
    }


def explain_correction(rule_id: str, category: str = "") -> Optional[GrammarTopic]:
    """Map a LanguageTool ruleId/category to a knowledge-base topic
    (used for the 'Why is this wrong?' button in the Grammar Checker tab)."""
    key_candidates = [rule_id.upper() if rule_id else "", category.upper() if category else ""]
    for key in key_candidates:
        for hint, topic_id in _LT_HINT_INDEX.items():
            if hint in key or key in hint:
                return next(t for t in KNOWLEDGE_BASE if t.id == topic_id)
    return None


# ==========================================================================
# SECTION 2: QUIZ BANK
# ==========================================================================

@dataclass
class QuizQuestion:
    id: str
    topic: str
    question: str
    options: List[str]
    correct_index: int
    explanation: str


QUESTION_BANK: List[QuizQuestion] = [
    QuizQuestion("q1", "Subject-Verb Agreement", "Which sentence is grammatically correct?",
                 ["He play cricket.", "He plays cricket.", "He playing cricket."], 1,
                 "'He' is third-person singular, so the simple present verb takes -s: 'plays'."),
    QuizQuestion("q2", "Has vs Have", "Choose the correct sentence.",
                 ["She have two brothers.", "She has two brothers.", "She having two brothers."], 1,
                 "With he/she/it, use 'has' instead of 'have'."),
    QuizQuestion("q3", "Is vs Are vs Am", "Fill in the blank: They ___ playing football.",
                 ["is", "am", "are"], 2,
                 "'They' is plural, so it pairs with 'are'."),
    QuizQuestion("q4", "Was vs Were", "Fill in the blank: We ___ at the party last night.",
                 ["was", "were", "is"], 1,
                 "'We' takes 'were' in the past tense of 'to be'."),
    QuizQuestion("q5", "Present Continuous", "Which sentence correctly uses the present continuous tense?",
                 ["I am go to school.", "I am going to school.", "I going to school."], 1,
                 "Present continuous needs 'am/is/are' + verb-ing: 'am going'."),
    QuizQuestion("q6", "Simple Past Tense", "Choose the correct past-tense sentence.",
                 ["Yesterday I goed to the market.", "Yesterday I went to the market.",
                  "Yesterday I go to the market."], 1,
                 "'Go' is irregular; its past tense is 'went', not 'goed'."),
    QuizQuestion("q7", "Articles", "Which sentence uses the correct article?",
                 ["I saw a elephant.", "I saw an elephant.", "I saw the elephant near river."], 1,
                 "'Elephant' starts with a vowel sound, so it takes 'an'."),
    QuizQuestion("q8", "Articles", "Choose the correct sentence.",
                 ["She is an university student.", "She is a university student.",
                  "She is the university student a."], 1,
                 "'University' starts with a consonant *sound* (yoo-), so it takes 'a', not 'an'."),
    QuizQuestion("q9", "Prepositions", "Fill in the blank: The meeting is ___ 5 PM.",
                 ["in", "on", "at"], 2,
                 "Use 'at' for precise clock times."),
    QuizQuestion("q10", "Its vs It's", "Which sentence is correct?",
                 ["The dog wagged it's tail.", "The dog wagged its tail.",
                  "The dog wagged its' tail."], 1,
                 "'Its' (no apostrophe) shows possession here, not the contraction 'it is'."),
    QuizQuestion("q11", "Comparatives", "Which sentence is grammatically correct?",
                 ["This book is more good than that one.", "This book is gooder than that one.",
                  "This book is better than that one."], 2,
                 "'Good' has an irregular comparative form: 'better', not 'more good' or 'gooder'."),
    QuizQuestion("q12", "Double Negatives", "Which sentence avoids a double negative?",
                 ["I don't have no money.", "I don't have any money.", "I don't have none money."], 1,
                 "Standard English uses only one negative marker per clause: 'don't ... any'."),
]


def get_topics() -> List[str]:
    return sorted({q.topic for q in QUESTION_BANK})


def build_quiz(topic: Optional[str] = None, num_questions: int = 5) -> List[QuizQuestion]:
    pool = [q for q in QUESTION_BANK if topic in (None, "All Topics", q.topic)]
    if not pool:
        pool = QUESTION_BANK[:]
    random.shuffle(pool)
    return pool[:min(num_questions, len(pool))]


def grade_answer(question: QuizQuestion, selected_index: int) -> bool:
    return selected_index == question.correct_index


# ==========================================================================
# SECTION 3: GRAMMAR CHECKER (LanguageTool — free public endpoint, no key)
# ==========================================================================

@dataclass
class GrammarIssue:
    message: str
    rule_id: str
    category: str
    bad_text: str
    suggestions: List[str]
    offset: int
    length: int


@functools.lru_cache(maxsize=1)
def _get_tool():
    """Create (and cache) a LanguageTool client. No API key is used anywhere:
    this either calls LanguageTool's free public endpoint, or — only if that
    is unreachable — spins up a local LanguageTool server (requires Java)."""
    if language_tool_python is None:
        raise RuntimeError(
            "language_tool_python is not installed. Run: pip install language-tool-python"
        )
    public_api_error = None
    try:
        tool = language_tool_python.LanguageToolPublicAPI("en-US")
        tool.check("This is a test.")
        return tool
    except Exception as e:
        public_api_error = e

    try:
        return language_tool_python.LanguageTool("en-US")
    except Exception as local_error:
        raise RuntimeError(
            "Could not reach LanguageTool's free public API "
            f"({public_api_error}), and the local fallback also failed "
            f"({local_error}). Either check your internet connection, or "
            "install Java to enable the offline local checker (see README)."
        ) from local_error


def check_text(text: str) -> List[GrammarIssue]:
    if not text or not text.strip():
        return []
    tool = _get_tool()
    matches = tool.check(text)
    issues = []
    for m in matches:
        bad_text = text[m.offset: m.offset + m.errorLength]
        issues.append(
            GrammarIssue(
                message=m.message,
                rule_id=getattr(m, "ruleId", "") or "",
                category=getattr(m, "category", "") or "",
                bad_text=bad_text,
                suggestions=list(m.replacements)[:5],
                offset=m.offset,
                length=m.errorLength,
            )
        )
    return issues


def correct_text(text: str) -> str:
    if not text or not text.strip():
        return text
    tool = _get_tool()
    matches = tool.check(text)
    return language_tool_python.utils.correct(text, matches)


CHECKER_AVAILABLE = language_tool_python is not None


# ==========================================================================
# SECTION 4: STREAMLIT APP (UI)
# ==========================================================================

st.set_page_config(page_title="Smart English Writing Assistant", page_icon="📝", layout="wide")


def _init_state():
    defaults = {
        "qa_history": [],
        "quiz_questions": [],
        "quiz_index": 0,
        "quiz_answers": {},
        "quiz_submitted": {},
        "quiz_score": 0,
        "quiz_attempts": 0,
        "topics_covered": set(),
        "last_issues": [],
        "last_checked_text": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


def _start_quiz_from_qa(topic: str):
    st.session_state.quiz_questions = build_quiz(topic=topic, num_questions=3)
    st.session_state.quiz_index = 0
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = {}


# ---- Sidebar ----
st.sidebar.title("📝 Smart English Writing Assistant")
st.sidebar.caption("Grammar Error Correction · Grammar Q&A · Interactive Learning")
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Your Session Progress")
st.sidebar.metric("Questions Asked", len(st.session_state.qa_history))
st.sidebar.metric("Quiz Questions Attempted", st.session_state.quiz_attempts)
if st.session_state.quiz_attempts:
    acc = 100 * st.session_state.quiz_score / st.session_state.quiz_attempts
    st.sidebar.metric("Quiz Accuracy", f"{acc:.0f}%")
else:
    st.sidebar.metric("Quiz Accuracy", "—")
if st.session_state.topics_covered:
    st.sidebar.caption("Topics covered: " + ", ".join(sorted(st.session_state.topics_covered)))

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset session progress"):
    for k in ["qa_history", "quiz_questions", "quiz_index", "quiz_answers",
              "quiz_submitted", "quiz_score", "quiz_attempts", "topics_covered",
              "last_issues", "last_checked_text"]:
        del st.session_state[k]
    _init_state()
    st.rerun()


# ---- Tabs ----
tab_checker, tab_qa, tab_quiz, tab_progress = st.tabs(
    ["✅ Grammar Checker", "💬 Grammar Q&A", "🧠 Practice Quiz", "📈 Learning Progress"]
)

# TAB 1: Grammar Checker
with tab_checker:
    st.header("Grammar Checker")
    st.write("Paste a sentence or paragraph below to detect and correct grammar errors.")

    text_input = st.text_area("Your text", height=150,
                               placeholder="e.g. She go to college and have a car.")

    if st.button("Check Grammar", type="primary"):
        if not CHECKER_AVAILABLE:
            st.error("The grammar checker isn't available. Install with: "
                      "`pip install language-tool-python`")
        elif not text_input.strip():
            st.warning("Please enter some text first.")
        else:
            with st.spinner("Checking grammar..."):
                start = time.time()
                checker_failed = False
                try:
                    issues = check_text(text_input)
                    corrected = correct_text(text_input)
                except Exception as e:
                    issues, corrected = [], text_input
                    checker_failed = True
                    st.error(f"Grammar checker error: {e}")
                elapsed = time.time() - start

            st.session_state.last_issues = issues
            st.session_state.last_checked_text = text_input

            if checker_failed:
                pass  # error already shown above; don't also claim success
            elif not issues:
                st.success("✅ No grammar issues found! Your text looks good.")
            else:
                st.warning(f"Found {len(issues)} issue(s) in {elapsed:.1f}s.")
                st.subheader("Corrected text")
                st.info(corrected)

                st.subheader("Details")
                for i, issue in enumerate(issues):
                    with st.expander(f"Issue {i+1}: \"{issue.bad_text}\" — {issue.message}"):
                        st.write(f"**Suggestion(s):** {', '.join(issue.suggestions) or '—'}")
                        st.write(f"**Rule ID:** `{issue.rule_id}`")
                        if st.button("❓ Why is this wrong?", key=f"why_{i}"):
                            topic = explain_correction(issue.rule_id, issue.category)
                            if topic:
                                st.session_state.topics_covered.add(topic.title)
                                st.markdown(f"**{topic.title}**")
                                st.write(topic.explanation)
                                st.caption(f"Rule: {topic.rule}")
                                st.write(f"❌ {topic.example_wrong}")
                                st.write(f"✅ {topic.example_right}")
                            else:
                                st.write(issue.message)
                                st.caption(
                                    "No detailed grammar-topic match found for this rule yet — "
                                    "try asking about it directly in the Grammar Q&A tab."
                                )

    if not CHECKER_AVAILABLE:
        st.caption(
            "⚠️ `language_tool_python` is not installed in this environment. "
            "Run `pip install -r requirements.txt` to enable this tab."
        )

# TAB 2: Grammar Q&A
with tab_qa:
    st.header("Grammar Q&A")
    st.write("Ask any grammar question in plain English, e.g. "
              "*\"Why do we use has instead of have?\"* or *\"When should I use a, an, and the?\"*")

    with st.form("qa_form", clear_on_submit=True):
        question = st.text_input("Your question")
        submitted = st.form_submit_button("Ask")

    if submitted and question.strip():
        start = time.time()
        result = answer_question(question)
        elapsed = time.time() - start

        record = {"question": question, "response_time": elapsed}
        if result["matched"]:
            topic = result["topic"]
            st.session_state.topics_covered.add(topic.title)
            record["answer"] = result["answer"]
            record["topic"] = topic.title
        else:
            record["answer"] = result["answer"]
            record["topic"] = None
        st.session_state.qa_history.append(record)

    if not st.session_state.qa_history:
        st.info("No questions asked yet in this session. Try one of the examples above!")
    for record in reversed(st.session_state.qa_history):
        st.markdown(f"**🧑 You:** {record['question']}")
        st.markdown(f"**🤖 Assistant:** {record['answer']}")
        if record.get("topic"):
            st.caption(f"Topic: {record['topic']}  ·  {record['response_time']*1000:.0f} ms")
            matching_qs = [q for q in QUESTION_BANK if q.topic == record["topic"]]
            if matching_qs:
                st.button(
                    f"🧠 Try a practice question on '{record['topic']}'",
                    key=f"practice_from_qa_{record['question']}_{record['response_time']}",
                    on_click=lambda t=record["topic"]: _start_quiz_from_qa(t),
                )
        st.markdown("---")

# TAB 3: Practice Quiz
with tab_quiz:
    st.header("Practice Quiz")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        topic_choice = st.selectbox("Topic", ["All Topics"] + get_topics())
    with col2:
        num_q = st.number_input("Number of questions", min_value=1, max_value=10, value=5)
    with col3:
        st.write("")
        st.write("")
        if st.button("🎯 Start / Restart Quiz"):
            st.session_state.quiz_questions = build_quiz(
                topic=None if topic_choice == "All Topics" else topic_choice,
                num_questions=num_q,
            )
            st.session_state.quiz_index = 0
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = {}

    st.markdown("---")

    quiz_qs = st.session_state.quiz_questions
    if not quiz_qs:
        st.info("Click **Start / Restart Quiz** to generate practice questions.")
    else:
        idx = st.session_state.quiz_index
        if idx >= len(quiz_qs):
            correct = sum(
                1 for q in quiz_qs
                if st.session_state.quiz_answers.get(q.id) == q.correct_index
            )
            st.success(f"🎉 Quiz complete! You scored {correct}/{len(quiz_qs)}.")
            for q in quiz_qs:
                sel = st.session_state.quiz_answers.get(q.id)
                is_correct = sel == q.correct_index
                icon = "✅" if is_correct else "❌"
                with st.expander(f"{icon} {q.question}"):
                    st.write(f"Your answer: {q.options[sel] if sel is not None else '—'}")
                    st.write(f"Correct answer: {q.options[q.correct_index]}")
                    st.caption(q.explanation)
        else:
            q = quiz_qs[idx]
            st.subheader(f"Question {idx + 1} of {len(quiz_qs)}  ·  Topic: {q.topic}")
            st.write(q.question)

            already_submitted = st.session_state.quiz_submitted.get(q.id, False)
            selected = st.radio(
                "Choose one:",
                options=list(range(len(q.options))),
                format_func=lambda i: f"{chr(65+i)}. {q.options[i]}",
                key=f"radio_{q.id}",
                disabled=already_submitted,
            )

            if not already_submitted:
                if st.button("Check answer", key=f"check_{q.id}"):
                    st.session_state.quiz_answers[q.id] = selected
                    st.session_state.quiz_submitted[q.id] = True
                    st.session_state.quiz_attempts += 1
                    st.session_state.topics_covered.add(q.topic)
                    if grade_answer(q, selected):
                        st.session_state.quiz_score += 1
                    st.rerun()
            else:
                sel = st.session_state.quiz_answers[q.id]
                if grade_answer(q, sel):
                    st.success(f"✅ Correct! {q.explanation}")
                else:
                    st.error(
                        f"❌ Not quite. Correct answer: "
                        f"{chr(65+q.correct_index)}. {q.options[q.correct_index]}\n\n{q.explanation}"
                    )
                if st.button("Next question ➡️", key=f"next_{q.id}"):
                    st.session_state.quiz_index += 1
                    st.rerun()

# TAB 4: Learning Progress
with tab_progress:
    st.header("Learning Progress & Evaluation")

    c1, c2, c3 = st.columns(3)
    c1.metric("Questions Asked (Q&A)", len(st.session_state.qa_history))
    c2.metric("Quiz Questions Attempted", st.session_state.quiz_attempts)
    acc = (100 * st.session_state.quiz_score / st.session_state.quiz_attempts
           if st.session_state.quiz_attempts else 0)
    c3.metric("Quiz Accuracy", f"{acc:.0f}%")

    st.subheader("Q&A History")
    if st.session_state.qa_history:
        df = pd.DataFrame(st.session_state.qa_history)
        df["response_time_ms"] = (df["response_time"] * 1000).round(0)
        st.dataframe(df[["question", "topic", "response_time_ms"]], use_container_width=True)
        st.caption(f"Average response time: {df['response_time_ms'].mean():.0f} ms")
    else:
        st.info("No Q&A activity yet.")

    st.subheader("Quiz Results (current session)")
    if st.session_state.quiz_questions and st.session_state.quiz_submitted:
        rows = []
        for q in st.session_state.quiz_questions:
            if q.id in st.session_state.quiz_submitted:
                sel = st.session_state.quiz_answers.get(q.id)
                rows.append({
                    "topic": q.topic,
                    "question": q.question,
                    "correct": grade_answer(q, sel) if sel is not None else False,
                })
        if rows:
            qdf = pd.DataFrame(rows)
            st.dataframe(qdf, use_container_width=True)
            st.bar_chart(qdf.groupby("topic")["correct"].mean())
    else:
        st.info("No quiz activity yet.")

    st.subheader("Topics Covered")
    if st.session_state.topics_covered:
        st.write(", ".join(sorted(st.session_state.topics_covered)))
    else:
        st.info("No topics covered yet.")
