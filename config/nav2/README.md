# Nav2 Config Notes

This folder contains templates for the future Nav2 integration stage.

Current project route:

```text
FAST-LIO localization
        ↓
map → odom → g1_base_link
        ↓
Nav2 planner / controller
        ↓
/g1/cmd_vel
        ↓
g1_proxy_bridge
        ↓
/cmd_vel in Isaac Sim
```

Do not treat `g1_nav2_params.template.yaml` as a final working file yet. The next engineering step is to define the TF ownership between FAST-LIO, `/g1/odom`, and Nav2.
