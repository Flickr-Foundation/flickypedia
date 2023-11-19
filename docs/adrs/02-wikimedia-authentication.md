# ADR #1: Authentication with Wikimedia

<table>
  <tr>
    <th>Author</th>
    <td>Alex Chan &lt;alex@flickr.org&gt;</td>
  </tr>
  <tr>
    <th>Originally written</th>
    <td>18 November 2023</td>
  </tr>
  <tr>
    <th>Last updated</th>
    <td>18 November 2023</td>
  </tr>
  <tr>
    <th>Status</th>
    <td>Implemented</td>
  </tr>
</table>

## Context

When Flickypedia uploads a photo to Wikimedia Commons (WMC), that upload should be associated with a WMC user.
This is better for users (who can see their uploads in their upload history) and prevents any risks associated with anonymous uploads (spam, vandalism, license washing).

Flickypedia needs a way for a user to authenticate with WMC, and to upload photos on their behalf.



## Desirable outcomes

There are some basic functional requirements for Flickypedia to work correctly:

*   Users can log in to Flickypedia, allowing it to perform uploads on their behalf.
*   Users can easily log out, and revoke Flickypedia's access.

There are also several technical requirements which we want from a security perspective:

*   We don't want Flickypedia to be used to compromise Wikimedia user accounts.
    For example, we're going to get permission to make edits on a user's behalf – we don't want this permission to be misused to make vandal edits in their name.
*   This needs to work when Flickypedia only runs on a single instance.
    We're going to run Flickypedia on a Mac Mini server in our London office, so we can't e.g. rely on the existence of some external "secure database" which is separate from the web server.
*   We only have a single developer, and no dedicated security team, so we need to keep it simple.
    That means no rolling our own crypto, inventing new token schemes, or other "clever ideas" – we should stick to existing approaches.

## Decisions

### OAuth 1.0a or OAuth 2?

MediaWiki supports [both OAuth 1.0a and OAuth 2.0][mediawiki_oauth].

The [Wikimedia API docs about Authentication][wikimedia_auth] recommend using the OAuth 2.0 authorization code flow:

> To allow your app to interact with and access content on behalf of a user, use the OAuth 2.0 authorization code flow.
> This provides a secure process for users to log in with their Wikimedia account and authorize your app.
> The OAuth 2.0 authorization code workflow can be used by server-side, client-side, and installed apps.

This is a well-trodden approach to authentication

[mediawiki_oauth]: https://www.mediawiki.org/wiki/OAuth/For_Developers
[wikimedia_auth]: https://api.wikimedia.org/wiki/Authentication

## Technical thinking

OAuth 1 vs OAuth 2
*   WMC offers both
*   https://www.mediawiki.org/wiki/OAuth/For_Developers
*   https://api.wikimedia.org/wiki/Authentication
*   OAuth 2 is default and simpler to implement
    => also I've done it before!

Library or roll own?
*   WMC describes how to do it: https://api.wikimedia.org/wiki/Authentication
*   But details are fiddly
*   Using authlib, which has httpx integration, esp around refresh tokens
*   What about mwoauth?
    AFAICT only supports OAuth 1
*   What about httpx-oauth?
    Unclear if maintained or widely used

Where do we call WMC APIs?
*   currently calling server-to-server, rather than from user's browser
*   many reasons, no-JS among them

How to store tokens?
*   OAuth 2.0 gives you access token, v powerful, allows you to make WM edits on behalf of user
*   Don't want to leak
*   Options:
    1.  Store in user session cookie
        Simple!
        But now these tokens go to user's browser, even though won't be used there – seems questionable, security-wise
        But now need to secure user's browser, so that eg browser extensions can't see tokens
        But session cookies have to be ≤4KB, WMC access token is almost that big!
    2.  Store in server-side DB, encrypted with central key
        Now tokens no longer in user's browser
        But token DB becomes SPOF
        In practice the token DB and Flickypedia app will run on same machine, which means encryption key will also live on that machine
        If you compromise that machine, all tokens
        Eek!
    3.  Store in server-side DB, encrypted with per-user key
        Encryption key generated at login time, stored in user session cookie
        =>  Whenever user is interacting with app, get key from session cookie + do stuff on their behalf
        =>  If you compromise user's browser, you only get randomly generated key
        =>  If you compromise server-side DB, you only get encrypted tokens
        
Implementation details
*   User with key in cookie + no DB entry => logged out, log in again
*   When logout, delete session cookie + DB entry
*   Record login time in DB entry, allow to purge later
*   Always check OAuth token is active to ensure we can use it
