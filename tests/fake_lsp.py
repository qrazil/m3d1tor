#!/usr/bin/env python3
"""A scripted language server for the end-to-end tests (tests/e2e.py).

Full-document sync. Every line containing BUG is a diagnostic. hover answers
"hover L:C", definition points at line 0, references at lines 0 and 2, rename
replaces every `hello` with the new name, formatting upper-cases the document,
code actions offer to delete the word BUG.
"""
import json
import sys

docs = {}


def read():
    header = sys.stdin.buffer.readline()
    if not header:
        return None
    length = int(header.split(b":")[1])
    sys.stdin.buffer.readline()
    return json.loads(sys.stdin.buffer.read(length))


def send(obj):
    data = json.dumps(obj).encode()
    sys.stdout.buffer.write(b"Content-Length: %d\r\n\r\n" % len(data) + data)
    sys.stdout.buffer.flush()


def reply(message, result):
    send({"jsonrpc": "2.0", "id": message["id"], "result": result})


def publish(uri):
    out = []
    for number, line in enumerate(docs.get(uri, "").split("\n")):
        column = line.find("BUG")
        if column >= 0:
            out.append({"range": {"start": {"line": number, "character": column},
                                  "end": {"line": number, "character": column + 3}},
                        "severity": 1, "message": "found BUG on line %d" % (number + 1)})
    send({"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics",
          "params": {"uri": uri, "diagnostics": out}})


def whole(uri):
    text = docs.get(uri, "")
    lines = text.split("\n")
    return {"start": {"line": 0, "character": 0},
            "end": {"line": len(lines) - 1, "character": len(lines[-1])}}


while True:
    message = read()
    if message is None:
        break
    method = message.get("method")
    params = message.get("params", {})
    if method == "initialize":
        reply(message, {"capabilities": {"hoverProvider": True, "definitionProvider": True,
                                         "referencesProvider": True, "renameProvider": True,
                                         "documentFormattingProvider": True,
                                         "codeActionProvider": True, "textDocumentSync": 1}})
    elif method == "textDocument/didOpen":
        document = params["textDocument"]
        docs[document["uri"]] = document["text"]
        publish(document["uri"])
    elif method == "textDocument/didChange":
        docs[params["textDocument"]["uri"]] = params["contentChanges"][-1]["text"]
        publish(params["textDocument"]["uri"])
    elif method == "textDocument/hover":
        position = params["position"]
        reply(message, {"contents": {"kind": "plaintext",
                                     "value": "hover %d:%d" % (position["line"], position["character"])}})
    elif method == "textDocument/definition":
        uri = params["textDocument"]["uri"]
        reply(message, [{"uri": uri, "range": {"start": {"line": 0, "character": 0},
                                              "end": {"line": 0, "character": 1}}}])
    elif method == "textDocument/references":
        uri = params["textDocument"]["uri"]
        reply(message, [{"uri": uri, "range": {"start": {"line": n, "character": 0},
                                              "end": {"line": n, "character": 1}}} for n in (0, 2)])
    elif method == "textDocument/rename":
        uri = params["textDocument"]["uri"]
        edits = []
        for number, line in enumerate(docs.get(uri, "").split("\n")):
            start = 0
            while True:
                column = line.find("hello", start)
                if column < 0:
                    break
                edits.append({"range": {"start": {"line": number, "character": column},
                                        "end": {"line": number, "character": column + 5}},
                              "newText": params["newName"]})
                start = column + 5
        reply(message, {"changes": {uri: edits}})
    elif method == "textDocument/formatting":
        uri = params["textDocument"]["uri"]
        reply(message, [{"range": whole(uri), "newText": docs.get(uri, "").upper()}])
    elif method == "textDocument/codeAction":
        uri = params["textDocument"]["uri"]
        edits = []
        for number, line in enumerate(docs.get(uri, "").split("\n")):
            column = line.find("BUG")
            if column >= 0:
                edits.append({"range": {"start": {"line": number, "character": column},
                                        "end": {"line": number, "character": column + 3}},
                              "newText": "FIXED"})
        reply(message, [{"title": "Fix BUG", "kind": "quickfix", "edit": {"changes": {uri: edits}}}])
    elif method == "shutdown":
        reply(message, None)
    elif method == "exit":
        break
    elif "id" in message and method is not None:
        reply(message, None)
