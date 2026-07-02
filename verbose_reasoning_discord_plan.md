# Verbose Reasoning Discord Option Implementation Plan

## Goal
Implement a verbose reasoning Hermes config Discord option that will expose all reasoning tokens for users.

## Background
The Discord integration was filtering out reasoning tokens (like `<REASONING_SCRATCHPAD>`, `</think>`, `<reasoning>`, etc.) through the `GatewayStreamConsumer._filter_and_accumulate()` method. This filtering was designed to suppress thinking blocks from the streaming display, but users wanted an option to see all reasoning tokens.

## Implementation Plan

### 1. Modify `StreamConsumerConfig` in `gateway/stream_consumer.py`
- Add `verbose_reasoning: bool = False` field to `StreamConsumerConfig` dataclass
- Update `_filter_and_accumulate()` method to skip think-block filtering when `verbose_reasoning` is True

### 2. Add Discord-specific config option in Discord adapter
- Add `_discord_verbose_reasoning()` method to `plugins/platforms/discord/adapter.py`
- Check `config.extra.get("verbose_reasoning")` or `DISCORD_VERBOSE_REASONING` environment variable

### 3. Wire the config into `StreamConsumerConfig` in `gateway/run.py`
- Pass the `verbose_reasoning` flag based on the platform config when creating `StreamConsumerConfig` instances

## What Has Been Accomplished So Far

### ✅ Completed Changes:

1. **`gateway/stream_consumer.py`**:
   - Added `verbose_reasoning: bool = False` to `StreamConsumerConfig` dataclass
   - Updated `_filter_and_accumulate()` method to skip think-block filtering when `self.cfg.verbose_reasoning` is True

2. **`plugins/platforms/discord/adapter.py`**:
   - Added `_discord_verbose_reasoning()` method that checks:
     - `self.config.extra.get("verbose_reasoning")` 
     - Falls back to `DISCORD_VERBOSE_REASONING` environment variable

3. **`gateway/run.py`**:
   - Wired `_verbose_reasoning` into both `StreamConsumerConfig` instantiations:
     - First instance around line 15079 (proxy streaming path)
     - Second instance around line 16274 (interim consumer path)
   - Both check `source.platform == Platform.DISCORD and hasattr(_adapter, "_discord_verbose_reasoning")`

### ✅ Configuration Usage:

Users can enable verbose reasoning in their Discord config:
```yaml
platforms:
  discord:
    enabled: true
    token: "your-discord-token"
    extra:
      verbose_reasoning: true
```

Or via environment variable:
```bash
DISCORD_VERBOSE_REASONING=true
```

## Next Steps / Potential Issues to Investigate

1. **Verify streaming callbacks are properly wired in Discord adapter**:
   - The `GatewayStreamConsumer` receives deltas via `stream_delta_callback`
   - Need to ensure Discord adapter properly sets up `stream_delta_callback` on the agent

2. **Test the implementation**:
   - Verify that reasoning tokens are displayed when `verbose_reasoning: true`
   - Verify that reasoning tokens are still filtered when `verbose_reasoning: false` (default)

3. **Check for any other places where `StreamConsumerConfig` is instantiated**:
   - Ensure all instances are updated with the `verbose_reasoning` parameter

4. **Consider adding documentation**:
   - Document the new `verbose_reasoning` option in Discord platform documentation