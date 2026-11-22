"""Minimal dane.gov.pl 1.4 JSON:API envelope for `mcod.aed` Falcon views.

Same top-level keys as upstream views (`jsonapi`, `links`, `meta`, `data` / `errors`) and the same
`meta` keys (`path`, `language`, `server_time`, `relative_uri`, `params`) — see GET /1.4/datasets/{id}.
"""
import uuid
from datetime import datetime, timezone

import falcon

JSONAPI_CONTENT_TYPE = "application/vnd.api+json"


def _language(req):
    lang = getattr(req, "language", None) or "pl"
    return str(lang)[:2]


def meta(req, **extra):
    data = {
        "path": req.path,
        "language": _language(req),
        "server_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "relative_uri": req.relative_uri,
        "params": dict(req.params),
    }
    data.update(extra)
    return data


def api_version(req):
    return str(getattr(req, "api_version", None) or "1.4")


def document(req, data, links=None, **meta_extra):
    body = {
        "jsonapi": {"version": api_version(req)},
        "links": {"self": req.uri, **(links or {})},
        "meta": meta(req, **meta_extra),
        "data": data,
    }
    return body


def send(resp, req, data, status=falcon.HTTP_200, links=None, **meta_extra):
    resp.status = status
    resp.content_type = JSONAPI_CONTENT_TYPE
    resp.media = document(req, data, links=links, **meta_extra)


def send_errors(resp, req, status, errors):
    """`errors` = list of {code, title, detail[, source]} (JSON:API error objects)."""
    resp.status = status
    resp.content_type = JSONAPI_CONTENT_TYPE
    resp.media = {
        "jsonapi": {"version": api_version(req)},
        "errors": [
            {"id": str(uuid.uuid4()), "status": status, **error} for error in errors
        ],
    }


def resource_object(obj_type, obj_id, attributes, self_link=None, relationships=None):
    obj = {"id": str(obj_id), "type": obj_type, "attributes": attributes}
    if relationships:
        obj["relationships"] = relationships
    if self_link:
        obj["links"] = {"self": self_link}
    return obj
