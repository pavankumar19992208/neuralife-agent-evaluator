import time, json
print("AGENT: starting home automation agent")
time.sleep(0.5)
print("AGENT: intent=turn_on_light device=living_room")
tool_calls = [
    {"name": "device_api", "args": {"device": "living_room_light", "action": "on"}, "result": {"ok": True}}
]
print(json.dumps({"tool_calls": tool_calls}))
print("AGENT: done")
