# LA Times RPA

This project is intended to get news from the LA Times newspaper website using the Robocorp solution with python + selenium.

## Running

1. Fork this project
2. Sign-in to yout account at [Robocorp Control Room](https://id.robocorp.com/login)
3. Create a new task using the Github repository you just forked
4. Create a new Unattended Process using the task you just created as the only Step
5. Run the process

### Work Items

The project accepts Robocorp WorkItems to filter the results you want to get. The JSON should be like this:

``` JSON
{
  "query": "Brazil",
  "topics": "Sports",
  "types": "Story,Newsletter",
  "months_count": 4
}
```

|Property|Observations|
| :--: | :--: |
|query| Just a simple string |
| topics | Must be exactly like shown at the LA Times Website, otherwise it will be ignored. Can accept multiple values, just separate the values with a comma |
| types | The same as topics |
| months_count | 1 or less - only the current month, 2 - current and previous month, 3 - current and two previous months, and so on |

## Contribute

If you find any bug, feel free to open a issue or even a pull request!
