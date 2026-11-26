
import os
import json
import certifi
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(".env", override=True)

os.environ["SSL_CERT_FILE"] = certifi.where()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE")

with open("schemes.json", "r", encoding="utf-8") as file:
    schemes = json.load(file)


def get_value(details, start, end):
    if start in details:
        value = details.split(start, 1)[1]
        value = value.split(end, 1)[0].strip()

        if value.lower() not in ["", "-", "na", "n/a"]:
            return value

    return ""


driver = GraphDatabase.driver(
    uri, auth=(username, password)
)

with driver.session(database=database) as session:

    for scheme in schemes:

        details = scheme["details"]
        source = scheme["source"]

        department = get_value(
            details,
            "Concerned Department:",
            "Concerned District:"
        )

        beneficiary = get_value(
            details,
            "Beneficiaries:",
            "Types of Benefits:"
        )

        benefit = get_value(
            details,
            "Types of Benefits:",
            "Eligibility criteria:"
        )

        sponsor = get_value(
            details,
            "Sponsered By:",
            "Funding Pattern:"
        )

        session.run(
            """
            MERGE (g:Government {name: 'Tamil Nadu Government'})
            MERGE (s:Scheme {source: $source})
            SET s.name = $name,
                s.details = $details
            MERGE (g)-[:OFFERS]->(s)
            """,
            name=scheme["scheme_name"],
            details=details,
            source=source
        ).consume()

        if department:
            session.run(
                """
                MATCH (s:Scheme {source: $source})
                MERGE (d:Department {name: $department})
                MERGE (s)-[:MANAGED_BY]->(d)
                """,
                source=source,
                department=department
            ).consume()

        if beneficiary:
            session.run(
                """
                MATCH (s:Scheme {source: $source})
                MERGE (b:Beneficiary {name: $beneficiary})
                MERGE (s)-[:HAS_BENEFICIARY]->(b)
                """,
                source=source,
                beneficiary=beneficiary
            ).consume()

        if benefit:
            session.run(
                """
                MATCH (s:Scheme {source: $source})
                MERGE (b:Benefit {name: $benefit})
                MERGE (s)-[:PROVIDES]->(b)
                """,
                source=source,
                benefit=benefit
            ).consume()

        if sponsor:
            session.run(
                """
                MATCH (s:Scheme {source: $source})
                MERGE (sp:Sponsor {name: $sponsor})
                MERGE (s)-[:SPONSORED_BY]->(sp)
                """,
                source=source,
                sponsor=sponsor
            ).consume()

        print("Updated:", scheme["scheme_name"])

driver.close()

print("Total schemes processed:", len(schemes))
print("Knowledge graph updated successfully!")
