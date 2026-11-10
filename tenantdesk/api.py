import os
from fastapi import Depends, Header
from pydantic import BaseModel, ConfigDict, Field
from .runtime import make_app, settings
from .service import TenantService

app, auth, reviewer = make_app("TenantDesk")


def service():
    config = settings()
    if config.get("TENANTDESK_DATABASE_URL"):
        from .postgres import PostgresStore

        return TenantService(
            store=PostgresStore(
                config["TENANTDESK_DATABASE_URL"],
                config.get("TENANTDESK_ADMIN_DATABASE_URL", ""),
            )
        )
    return TenantService(
        os.path.join(os.environ.get("DATA_DIR", ".data"), "tenantdesk.db")
    )


class Tenant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    quota: int = Field(default=100, ge=1, le=10000)


class Document(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=100000)


class Chat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=2000)
    request_key: str = Field(min_length=1, max_length=100)
    live: bool = False


class Lead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    email: str
    consent: bool


@app.post("/admin/tenants", dependencies=[Depends(auth)])
def create(body: Tenant):
    return service().create_tenant(**body.model_dump())


@app.put("/documents/{identifier}")
def document(identifier: str, body: Document, authorization: str = Header(default="")):
    return service().put_document(
        authorization.removeprefix("Bearer "), identifier, body.title, body.text
    )


@app.delete("/documents/{identifier}")
def delete(identifier: str, authorization: str = Header(default="")):
    service().delete_document(authorization.removeprefix("Bearer "), identifier)
    return {"deleted": identifier}


@app.post("/chat")
def chat(body: Chat, authorization: str = Header(default="")):
    return service().chat(authorization.removeprefix("Bearer "), **body.model_dump())


@app.post("/leads")
def lead(body: Lead, authorization: str = Header(default="")):
    return service().capture_lead(
        authorization.removeprefix("Bearer "), **body.model_dump()
    )


@app.get("/export")
def export(authorization: str = Header(default="")):
    return service().export(authorization.removeprefix("Bearer "))
