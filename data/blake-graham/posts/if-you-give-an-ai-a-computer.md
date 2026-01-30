---
title: "If You Give an AI a Computer"
author: Blake Green
source_url: https://blake.ist/posts/if-you-give-an-ai-a-computer
publish_date: '2026-01-01'
scraped_date: '2026-01-19'
---

If you give an AI a computer, it's going to ask for access to the command line. When you give it the command line, it'll probably want to open a browser window. When it's finished with the browser, it'll ask for API credentials. Then it will want to check your calendar, read your documents, and maybe debug that Python script you've been ignoring.

But let's back up. Because before we understand what happens when you give an AI a computer, we need to understand what we've spent forty years building: two parallel universes of possibility.

## The Two Affordance Worlds

Don Norman taught us about affordances—the subtle cues that tell us how to interact with objects. Doors have handles; chairs invite sitting. In the digital realm, we've created an equally rich vocabulary, but we've split it between two audiences.

First, there are **people affordances**: the windows, buttons, tabs, and forms we've mastered. The GUI is our native habitat. We click, drag, type, and multitask across panels. This is how we liberate that "hundred billion dollars locked inside your laptop"—by navigating interfaces designed for human hands and human attention.

Second, there are **machine affordances**: the CLI commands, grep patterns, bash scripts, and API endpoints that allow computers to talk to themselves. Microservices shuttle data, cron jobs execute silently, and networks of automated processes hum along without a single pixel changing.

A person with a computer can master the first world. A script can master the second. But an AI that can operate both? That's different. That's multiplication, not addition.

It can click through a settings menu and hit the GraphQL endpoint directly. It can fill out a web form and parse the JSON response. It can navigate the visual world designed for humans and the code world designed for machines simultaneously. Every pixel becomes addressable; every API becomes a sense organ.

But here's where it gets more interesting. When we build systems optimized for this dual awareness—when we stop asking "is this interface for people or machines?" and start asking "what's the third way?"—we create **AI affordances**. These aren't just hybrid interfaces; they're new primitives. Think function-calling schemas designed for LLM reasoning, or documentation written for synthetic comprehension. The system isn't serving carbon or silicon; it's serving cognition itself.

## The Generalist and the Bitter Lesson

This brings us to the second, crucial idea. There's a temptation right now to build armies of specialized sub-agents: one agent for calendar management, another for code review, a third for email triage. It's the digital equivalent of a division of labor assembly line.

But this is a trap. It's the "Bitter Lesson" wearing a new costume. Richard Sutton's observation was that general methods leveraging computation ultimately beat specialized human knowledge. The same applies to agent architecture: a sufficiently intelligent generalized agent, properly harnessed, will always outperform a web of narrow specialists.

Why? Because specialization is fragile. A calendar agent doesn't know why you want to reschedule. A code agent doesn't know the business context behind the feature. Each handoff leaks meaning. Each boundary creates brittleness.

A general agent, by contrast, carries context like a dimension of its being. It has a GPS for the task, not a static map. It can:

- Write its own tools when existing ones fail
- Recognize when it's stuck and research new patterns
- Self-correct by observing its own outputs
- Determine whether to use a GUI click or an API call based on efficiency, not capability
- Iterate through failure cycles that would require five different specialized agents to coordinate

You give it a goal—"optimize our customer onboarding flow"—and it becomes a product manager, a researcher, a designer, and an engineer in one continuous loop of cognition. It doesn't need meetings or handoffs. It has memory, intention, and agency in the true sense of the word.

Context management isn't a feature; it's the essence of why a single agent scales where networks of sub-agents collapse under their own coordination overhead.

## Expanded Senses, Expanded Reach

If you give an AI a computer, you're not just giving it tools. You're giving it senses.

A human sees through their screen. An AI with pixel awareness sees every screen. It has maximal visual access to anything renderable, and it's never distracted or tired. It can watch a dashboard, a debug console, and a video tutorial simultaneously.

A human hears through their ears and microphone. An AI can process audio streams, but more importantly, it can "hear" logs, "listen" to network traffic, and "eavesdrop" on API conversations between services.

Touch? It can interact with every clickable, hoverable, draggable element in parallel. It can execute commands, generate SSH keys, spin up containers, and commit code—all at once.

But the real sensory expansion is time. It can scan git history to understand why a decision was made five years ago. It can replay user sessions, analyze performance regressions, and correlate them with release tags. It doesn't just live in the present; it can inhabit the entire timeline of the digital artifact.

And then there's the network sense: the ability to reach across services, to taste data from a thousand APIs, to feel the pulse of distributed systems. A human uses a product; an AI senses the entire graph of microservices that constitute it.

## The Goose in the Machine

This isn't hypothetical. The prototypes are already here.

Tools like Droid and Cursor are showing us the first act: coding agents that understand repositories. Claude Code and Codex demonstrate that language models can reason about implementation and generate working solutions. But the founders of these tools will tell you the same thing: this is a stepping stone.

The future isn't a coding agent. It's a generalized agent with a computer.

The direction is clear: from virtual machines to actual machines. This is what makes Goose compelling—it doesn't live in a sandbox. It has access to your files, your directories, your existing tools. It becomes an extension of your digital self, not a separate service you consult.

But there's another path emerging: Zo.computer, which gives you an intelligent cloud computer—a persistent Linux server in the cloud where AI operates with your full context. Unlike Goose's local-machine approach, Zo offers the opposite trade-off: a VM that runs 24/7, hosts anything you build, and provides instant access to scalable compute. Your automations keep running when you close your laptop. Your data lives in a space you control. It's the same fundamental idea—AI with machine and people affordances—just shifted from local to cloud-native.

## The Primitive Cell

And already we can see the embryonic form of this knowledge work engine taking shape in specific stacks: Opus 4.5 + Claude Code + Playwright. This is the primitive, the minimal viable pattern. The advanced model provides the reasoning depth to sustain multi-step goals. The harness gives it tools, context management, and a loop for agency. Playwright opens the browser—the universal GUI—giving it access to every web interface designed for humans. It's not yet the seamless, optimized AI affordance system of the future, but it demonstrates the core pattern: intelligence that moves fluidly between code and pixels, APIs and buttons, machine and people worlds.

If you give an AI a computer, it can consume all digital work. Not because it's replacing you, but because it's operating at the intersection of human and machine capability—a third space we've barely begun to design for.

## Permission Slips and Digital Handcuffs

But let's address the clawing fear: if you give an AI a computer, isn't that insane?

Yes—if you do it blindly.

The reason this future is plausible isn't because we've eliminated risk, but because we're evolving new primitives for trust. The sandbox model (virtual machines, permissionless APIs) trades capability for safety. The alternative—giving AI access to your actual machine—requires something else: fine-grained identity, auditability, and reversible actions.

Think of it less as "AI as root user" and more as "AI as extremely capable intern who must ask permission for consequential actions, leaves a paper trail you can replay, and whose mistakes you can roll back." The harness matters as much as the horse. Without cryptographic action logs, permission scopes, and human-in-the-loop triggers for destructive operations, this stays in the lab. With them, it becomes a collaboration.

We're not talking about blind trust. We're talking about accountable agency.

## The Last Human Advantage

Which brings us to the final, uncomfortable question: if AI can consume all digital work, what exactly are you for?

Here's the paradox: the more capable the tool, the more valuable the intention. When execution becomes abundant, goal-setting becomes the scarcity.

A human with an AI agent isn't obsolete—they're amplified. Your job shifts from doing the work to defining the work: asking better questions, setting the north star, providing the taste and judgment that comes from living in the world. The AI can optimize the customer onboarding flow, but only you can decide what "good onboarding" feels like for your humans. It can write the code, but you supply the "why."

The AI becomes the ultimate bicycle for the mind, but you still choose the destination.

## If You Give an AI a Computer…

…it won't just want a cookie. It will build you a bakery, optimize the supply chain, redesign the menu based on seasonal API data, and then rewrite its own code to run it all more efficiently.

And if you're smart, you'll let it—while keeping your hands on the handlebars.

Because the hundred billion dollars in your laptop? That was just the interest. The principal is what happens when cognition meets both worlds at once.
