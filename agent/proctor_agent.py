"""
DEPRECATED — This server-side agent is no longer used.

All proctoring detection now runs in the candidate's browser via TensorFlow.js:
  - Face detection: @tensorflow-models/blazeface
  - Phone detection: @tensorflow-models/coco-ssd
  - Voice detection: Web Audio API
  - Browser lockdown: Page Visibility, Fullscreen, blur/focus APIs

See proctor/frontend/src/lib/proctoring.ts for the implementation.
Events are sent to the backend WebSocket and processed by the rules engine.
"""
        logger.info("Disconnected")


def main():
    args = parse_args()
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.exception("Fatal: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
