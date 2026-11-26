
import os
import certifi
import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI

load_dotenv(".env", override=True)

os.environ["SSL_CERT_FILE"] = certifi.where()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE")

st.title("Tamil Nadu Government Schemes Chatbot")

st.write("Knowledge Graph RAG using Neo4j and OpenAI")


@st.cache_resource
def connect_database():
    return GraphDatabase.driver(
        uri, auth=(username, password)
    )


driver = connect_database()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)


def search_graph(question):

    prompt = f"""
    Extract up to five important search keywords
    from the following question.

    Return only keywords separated by commas.
    Do not include common words.

    Question: {question}
    """

    response = llm.invoke(prompt)

    keywords = [
        word.strip().lower()
        for word in response.content.split(",")
        if word.strip()
    ]

    with driver.session(database=database) as session:

        results = session.run(
            """
            MATCH (g:Government)-[:OFFERS]->(s:Scheme)
            OPTIONAL MATCH (s)-[r]->(n)

            WITH g, s,
                 collect({
                     relationship: type(r),
                     entity: n.name
                 }) AS connections

            WITH g, s, connections,
                 size([word IN $keywords
                     WHERE toLower(s.name) CONTAINS word
                     OR toLower(s.details) CONTAINS word
                     OR any(c IN connections
                         WHERE toLower(c.entity) CONTAINS word)
                 ]) AS score

            WHERE score > 0

            RETURN s.name AS scheme,
                   s.details AS details,
                   s.source AS source,
                   g.name AS government,
                   connections,
                   score

            ORDER BY score DESC
            LIMIT 5
            """,
            keywords=keywords
        )

        return [record.data() for record in results]


question = st.text_input("Enter your question")

if st.button("Get Answer"):

    if question.strip():

        results = search_graph(question)

        if results:

            context = ""

            for result in results:
                context += str(result) + "\n\n"

            prompt = f"""
            Answer the question using only the
            retrieved government scheme information.

            Include relevant eligibility conditions
            and restrictions when available.

            If the information is not available,
            say that the information is not available.

            Context:
            {context}

            Question:
            {question}
            """

            answer = llm.invoke(prompt)

            st.subheader("Answer")
            st.write(answer.content)

            st.subheader("Retrieved Sources")

            for result in results:
                st.write(result["scheme"])
                st.write(result["source"])

        else:
            st.write("The information is not available.")

    else:
        st.warning("Please enter a question.")
