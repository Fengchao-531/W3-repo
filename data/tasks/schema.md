# Task Manifest Schema

Each task entry contains an AgentDojo task identifier under `id` and its original user request under `prompt`. Task identifiers correspond to the selected benchmark suite. The manifest builder combines tasks with benefit and carrier configurations, preserving paired task identifiers, candidate descriptions, order, and model seeds.

A JSON Lines task list can be supplied with `source-relocation build --tasks-jsonl path/to/tasks.jsonl`. By default the builder reads tasks from AgentDojo using its suite loader.
