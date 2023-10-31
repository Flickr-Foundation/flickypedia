# ADR #1: Choosing Python and Flask

<table>
  <tr>
    <th>Author</th>
    <td>Alex Chan &lt;alex@flickr.org&gt;</td>
  </tr>
  <tr>
    <th>Originally written</th>
    <td>31 October 2023</td>
  </tr>
  <tr>
    <th>Last updated</th>
    <td>31 October 2023</td>
  </tr>
  <tr>
    <th>Status</th>
    <td>Accepted</td>
  </tr>
</table>

## Context

Flickypedia is being built as a brand new tool.
Its precursor, Flickr2Commons, is written using PHP, but we don't have to use any of that code in Flickypedia.

Initially there will only be one developer working on Flickypedia (me, Alex).
Longer term, Flickypedia will be maintained by the Flickr Foundation and their developers.

## Desirable outcomes

*   **We can get started on Flickypedia quickly.**
    The goal is to share an early version of Flickypedia at [GLAM Wiki 2023](https://meta.wikimedia.org/wiki/GLAM_Wiki_2023), and launch it publicly soon after that.

*   **It's easy to put Flickypedia down, and pick it back up again later.**
    Flickypedia isn't going to be the only software product the Foundation works on – after we launch the first version and address any immediate feedback, we're going to work on other things.

    When we come back to it later, it should be easy to pick up where we left off, even though we haven't been working on it continuously.
    That means good guard rails (automated tests, code checking, etc).

*   **Other software developers can work on Flickypedia (not just me!).**
    It should be possible to hire other developers who can maintain this codebase – I won't be the sole developer at the Flickr Foundation forever.

*   **Flickypedia should remain usable for a long time.**
    The [first commit](https://bitbucket.org/magnusmanske/flickr2commons/commits/245376f66afcf2e761094bbf68035dd0b1830b60) to Flickr2Commons was in June 2013, and it still works in October 2023.
    More than a decade!

    We should aim big – Flickypedia should still be in a working state come the end of 2033.

## Decision

**I chose Python and Flask as the programming language and framework to build Flickypedia.**
I've been working in Python for a long time, and I'm already familiar with Python idioms and the surrounding ecosystem.

This allows us to hit a lot of our desired outcomes:

*   **I can get started quickly.**
    I already know how to use Python and how to set up a Python project; I've done it lots of times.
    I can take that for granted, and focus on more Flickr-specific work.

*   **I can set up guard rails for Python projects.**
    I already know what the good, established tools are in the Python ecosystem for automated testing and the like.
    At time of writing, Flickypedia has:

    *   automated testing with [pytest](https://docs.pytest.org/en/latest/) and [GitHub Actions](https://github.com/features/actions), and coverage reporting from [coverage](https://github.com/nedbat/coveragepy)
    *   code autoformatting with [Black](https://github.com/psf/black)
    *   code linting with [flake8](https://github.com/pycqa/flake8)

    These won't catch all bugs, but they give me a safety net against regressions and silly mistakes.
    Because I already knew these tools, I was able to set them up and embed them in the project early.

*   **Python and Flask are popular tools, so there are lots of other developers who could work on the Flickypedia codebase.**
    This means that when the Foundation hires more software developers, whether to assist or to replace me, they should be able to find people who already know who are already somewhat familiar with these tools.

    And because I've worked on other Python projects and I know some common idioms, conventions, and pitfalls, hopefully I can write code which will be readable and sensible to another experienced Python developer.
    When other Python developers work on this project, I want it to feel familiar.

*   **I can pick dependencies which are likely to be maintained.**
    Because I've been working in Python for over a decade, I have some sense of which libraries we can probably trust to keep being developed and maintained.
    I can't rule it out, but I can reduce the likelihood of a key dependency being deprecated, broken, or discontinued.

    (I actually learnt Python and Flask a year or so before Flickr-to-Commons was being developed!)

## Alternatives considered

*   **Another language that I know.**
    Python is the language I'm most familiar with; there are only a handful of others I know well enough to consider something like Flickypedia:

    -   Scala: probably the language I know best after Python, but Scala devs are comparatively rare (would the Foundation be able to hire my replacement?) and I find the developer experience quite frustrating (long compile times).

    -   Ruby: I know it quite well, but it's similar to Python and I know Python better.
        I only pick Ruby over Python when there's a specific library or dependency that's Ruby-only, and that's not the case here.

    -   JavaScript/React: there are lots of developers using this stack, but I don't know it especially well.
        I've worked on several pre-existing React projects, but I wouldn't be confident setting up a new project and creating my guard rails.

*   **A language that I don't know.**
    That would be a risk – there's a high chance I'd make a mistake or write a codebase that's incomprehensible to a more experienced developer in that language.
    I could probably get something working, but we might struggle to find other developers who work on the codebase.

    I'm not sure there's a toolchain that's so-much-better than Python and Flask for this sort of web app that it would justify that risk.

    I could perhaps use PHP, which is used by Flickr-to-Commons, and reuse some of that code -- but I have almost no PHP experience, and I'm not convinced that PHP is better-enough than Python to be worth the switching risks.

    (Whereas if I was writing an iOS app, it would be worth learning Swift, which is a much better toolchain than Python for that sort of task.)
