
from fastapi import APIRouter, HTTPException

from app.database.neo4j import Neo4jDatabase
from app.database.graph_service import LegalMindGraphService


router = APIRouter(
    prefix="/graph",
    tags=["Knowledge Graph"]
)


def get_graph_service():
    """
    Create a Neo4j database connection and graph query service.
    """
    db = Neo4jDatabase()
    graph = LegalMindGraphService(db)

    return db, graph


@router.get("/documents")
def get_documents():
    """
    Return all contracts stored in the LegalMind knowledge graph.
    """

    db, graph = get_graph_service()

    try:
        return {
            "status": "success",
            "documents": graph.get_documents()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()


@router.get("/contracts/{contract_id}/clauses")
def get_contract_clauses(contract_id: int):
    """
    Return all clauses belonging to a contract.
    """

    db, graph = get_graph_service()

    try:
        return {
            "status": "success",
            "contract_id": contract_id,
            "clauses": graph.get_contract_clauses(contract_id)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()


@router.get("/contracts/{contract_id}/risks")
def get_contract_risks(contract_id: int):
    """
    Return all risk findings for a contract.
    """

    db, graph = get_graph_service()

    try:
        return {
            "status": "success",
            "contract_id": contract_id,
            "risks": graph.get_contract_risks(contract_id)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()


@router.get("/contracts/{contract_id}/high-risk")
def get_high_risk_clauses(contract_id: int):
    """
    Return high-risk findings for a contract.
    """

    db, graph = get_graph_service()

    try:
        return {
            "status": "success",
            "contract_id": contract_id,
            "high_risk": graph.get_high_risk_clauses(contract_id)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()


@router.get("/contracts/{contract_id}/risk-summary")
def get_risk_summary(contract_id: int):
    """
    Return risk counts grouped by severity.
    """

    db, graph = get_graph_service()

    try:
        summary = graph.get_risk_summary(contract_id)

        return {
            "status": "success",
            "contract_id": contract_id,
            "risk_summary": summary
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()


@router.get("/contracts/{contract_id}/overview")
def get_contract_overview(contract_id: int):
    """
    Return a complete knowledge-graph overview of a contract.
    """

    db, graph = get_graph_service()

    try:
        return {
            "status": "success",
            "overview": graph.get_contract_overview(contract_id)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()
