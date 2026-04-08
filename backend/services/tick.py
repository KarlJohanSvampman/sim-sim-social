import asyncio
from services.state import get_world, init_world
from services.ws import manager
from services.physiology import update_needs
from services.needs_locations import decide_goal
from services.perception import perceive
from services.attention import filter_attention
from services.belief import update_beliefs
from services.memory import recall, store
from services.memory_compression import compress_memories
from services.cognition import build_context
from services.llm import decide_action
from services.actions import execute
from services.deception import maybe_lie
from services.suspicion import update_suspicion
from services.gossip import propagate_gossip
from services.conversation import step_conversation
from services.hazards import tick_hazards, apply_hazard_damage
from services.emergency import dispatch_services
from services.addiction import tick_addiction

async def simulation_loop():
    world=get_world()
    init_world()
    while True:
        world["tick"] += 1
        tick_hazards(world)
        for c in world["characters"].values():
            update_needs(c)
            tick_addiction(c)
            apply_hazard_damage(world,c)
            c["goal"]=decide_goal(c, world)
        dispatch_services(world)
        chars=list(world["characters"].values())
        for c in chars:
            raw=perceive(c,world)
            focused=filter_attention(raw, bandwidth=4)
            update_beliefs(c,focused)
            decision=None
            if c.get("conversation_id"):
                step=step_conversation(world,c)
                if step:
                    decision={"plan":[step],"thoughts":"Conversation continues.","emotion_update":{}}
            if decision is None:
                if c.get("plan"):
                    decision={"plan":c["plan"],"thoughts":"Continuing existing plan.","emotion_update":{}}
                else:
                    context=build_context(c,focused,world)
                    context["memory"]=recall(c)
                    decision=decide_action(c,world,context)
                    c["plan"]=decision.get("plan",[])
            c["thoughts"]=decision.get("thoughts","...")
            execute(world,c,decision)
            if c.get("speech"):
                spoken=maybe_lie(c,c["speech"])
                c["speech"]=spoken["content"]
                for other in chars:
                    if other["id"]!=c["id"]:
                        update_suspicion(other,c["id"],spoken)
                propagate_gossip(c,chars,{"speech":spoken["content"],"is_lie":spoken["is_lie"]})
            store(c,{"tick":world["tick"],"decision":decision})
            if world["tick"] % 10 == 0:
                compress_memories(c)
        await manager.broadcast(world)
        await asyncio.sleep(1.0)
