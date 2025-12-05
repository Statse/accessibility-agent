# NVDA Log Format Documentation

## Log File Location

Default location: `%TEMP%\nvda.log` (typically `C:\Users\<username>\AppData\Local\Temp\nvda.log`)

## Log Entry Format

NVDA logs use the following format:

```
LEVEL - module.path (HH:MM:SS.mmm) ThreadName (LEVEL):
Message content
```

### Components:

1. **Log Level**: DEBUG, INFO, IO, WARNING, ERROR
2. **Module Path**: Python module path (e.g., `speech.speech.speak`, `inputCore.InputManager`)
3. **Timestamp**: Time in format `(HH:MM:SS.mmm)` - 24-hour format with milliseconds
4. **Thread Name**: Usually `MainThread`
5. **Log Level (repeated)**: Same as first level
6. **Message**: The actual log content (can be multi-line)

## Important Log Types

### Keyboard Input

```
IO - inputCore.InputManager.executeGesture (10:23:45.123) MainThread (INFO):
Input: kb(desktop):tab
```

Pattern: `Input: kb(desktop):<key>`

Common keys:
- `tab` - Tab key
- `shift+tab` - Shift+Tab
- `enter` - Enter key
- `escape` - Escape key
- `h` - H key (heading navigation)
- `k` - K key (link navigation)
- `d` - D key (landmark navigation)
- `f` - F key (form field navigation)
- `b` - B key (button navigation)

### Speech Output

```
DEBUG - speech.speech.speak (10:23:45.234) MainThread (DEBUG):
Speaking: ['Login button']
```

or

```
DEBUG - speech.speech.speak (10:23:45.234) MainThread (DEBUG):
Speaking: [u'Login button', u'pushbutton']
```

Pattern: `Speaking: [<text>]` or `Speaking: [u'<text>', u'<role>']`

The speech array can contain multiple elements:
- Element name/text
- Element role (button, link, edit, heading, etc.)
- Element state (checked, required, invalid, etc.)

### Multi-line Speech

```
DEBUG - speech.speech.speak (10:23:45.234) MainThread (DEBUG):
Speaking: [u'Welcome to our website',
 u'heading',
 u'level 1']
```

## Parsing Strategy

1. **Line-by-line reading**: Read log file line by line
2. **Regex matching**: Use regex to extract timestamp, level, module, message
3. **Multi-line handling**: Detect continuation lines (indented or starting with whitespace)
4. **Timestamp parsing**: Convert HH:MM:SS.mmm to datetime with millisecond precision
5. **Real-time monitoring**: Use file seeking and polling to read new entries

## Key Extraction Rules

### Keyboard Actions
- Look for lines with `Input: kb(desktop):`
- Extract key combination after colon
- Parse modifiers (shift, ctrl, alt) from key string

### Speech Output
- Look for lines with `Speaking: [`
- Extract text between quotes or brackets
- Handle Unicode prefix (`u'text'`)
- Combine multi-line speech arrays

## Edge Cases

1. **Startup logs**: NVDA logs configuration on startup
2. **Error messages**: Exception tracebacks can span many lines
3. **Empty speech**: `Speaking: []` indicates no speech output
4. **Repeated speech**: NVDA may announce same element multiple times
5. **Log rotation**: NVDA may rotate logs, watch for file changes
6. **Unicode characters**: Handle special characters in element names
7. **Time rollover**: Handle midnight rollover (00:00:00 after 23:59:59)

## Example Log Sequence

```
IO - inputCore.InputManager.executeGesture (14:23:45.123) MainThread (INFO):
Input: kb(desktop):tab

DEBUG - speech.speech.speak (14:23:45.234) MainThread (DEBUG):
Speaking: [u'Email', u'edit', u'blank']

IO - inputCore.InputManager.executeGesture (14:23:47.456) MainThread (INFO):
Input: kb(desktop):tab

DEBUG - speech.speech.speak (14:23:47.567) MainThread (DEBUG):
Speaking: [u'Password', u'edit', u'password', u'blank']

IO - inputCore.InputManager.executeGesture (14:23:50.789) MainThread (INFO):
Input: kb(desktop):enter

DEBUG - speech.speech.speak (14:23:50.890) MainThread (DEBUG):
Speaking: [u'Sign in', u'button']
```

## Correlation Rules

1. **Action → Feedback**: First speech output after keyboard input is correlated
2. **Timeout**: If no speech within 2 seconds, mark as timeout (potential accessibility issue)
3. **Latency**: Calculate time difference between input and speech
4. **Silence**: No speech output may indicate unlabeled element
