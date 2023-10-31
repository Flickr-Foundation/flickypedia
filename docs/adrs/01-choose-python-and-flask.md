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
Its precursor, Flickr-to-Commons, is written using PHP, but we don't have to use any of that code in Flickypedia.

Initially there will only be one developer working on Flickypedia (me, Alex).
Longer term, Flickypedia will be maintained by the Flickr Foundation and their developers.

## Desirable outcomes

*   **We can get started on Flickypedia quickly.**
    The goal is to share an early version of Flickypedia at [GLAM Wiki 2023](https://meta.wikimedia.org/wiki/GLAM_Wiki_2023), and ship an initial version by the end of 2023.

*   **It's easy to put Flickypedia down, and pick it back up again later.**
    Flickypedia isn't going to be the only software product the Foundation works on

## Decision

I chose Python and Flask as the programming language and framework to build Flickypedia.

The main reason is that **I'm already familiar with Python and the associated ecosystem**.

*   The immediate benefit is that **I can get started quickly**.

    I already know how to use Python and how to set up a Python project; I've done it lots of times.
    I can take that for granted, and focus on more Flickr-specific work.

*   It also allowed me to **set up guard rails**.

    I already know what the good, established tools are in the Python ecosystem for automated testing and the like.
    At time of writing, Flickypedia has:
    
    *   automated testing with [pytest](https://docs.pytest.org/en/latest/) and [GitHub Actions](https://github.com/features/actions), and coverage reporting from [coverage](https://github.com/nedbat/coveragepy)
    *   code autoformatting with [Black](https://github.com/psf/black)
    *   code linting with [flake8](https://github.com/pycqa/flake8)
    
    These won't catch all bugs, but they give me a safety net against regressions and silly mistakes.
    Because I already knew these tools, I was able to set them up and embed them in the project early.

*   Longer-term, I hope this makes it **easier for other developers to work on Flickypedia**.

    I've worked on other Python projects, and I know some common idioms, conventions, and pitfalls.
    I've written a lot of Python code and I have some sense of how to make my code understandable to other people.
    When other Python developers work on this project, I want it to feel familiar.

    If I'd picked a new-to-me toolchain, there's a much bigger chance I'd have done something weird or dangerous, and caused stumbling blocks for future developers.
    
    If it was a larger team, I'd be using code review to check that other people could understand my code.
    Although some people have generously offered to do some code review, I want to be careful not to overuse it – I'm producing a lot of code quickly, and I don't want to overwhelm somebody who doesn't have dedicated time for Flickypedia.

*   In turn, I hope this **ensures the longevity of Flickypedia.**

    I won't be working at the Flickr Foundation forever – at some point I'll leave, and another developer will take over my code.    
    Python is a popular language, and there are lots of qualified developers who could take over this codebase if I do it properly.
    If I picked something more esoteric or new-to-me, that would be much less likely.
    
    I'm also picking dependencies that I expect to last a long time.
    Python, Flask, and the associated libraries have been developed and maintained by the OSS community for a long time.
    It's reasonable to expect that they will continue to be maintained.

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
    
    I'm not sure there's a toolchain that's so-much-better than Python and Flask for this sort of web app that it would justify that risk.
    
    I could perhaps use PHP, which is used by Flickr-to-Commons, and reuse some of that code -- but I have almost no PHP experience, and I'm not convinced that PHP is better-enough than Python to be worth the switching cost.
    
    (Whereas if I was writing an iOS app, it would be worth learning Swift, which is a much better toolchain than Python for that sort of task.)
