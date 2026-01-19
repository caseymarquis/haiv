# My Process

## API Design

When creating new APIs (helpers, modules, commands):

1. **Find a real use case** - Identify actual calling code that will use this API
2. **Write ideal calling code** - Imagine the API exists and write the code you *wish* you could write. Don't worry about implementation - focus on clarity and ease of use for the caller
3. **Iterate on the surface** - Refine the imagined API until the calling code is exceptionally clear
4. **TDD the implementation** - Use standard TDD to implement the API, adjusting for practical constraints as needed

This consumer-first approach ensures APIs are designed for usability rather than implementation convenience
