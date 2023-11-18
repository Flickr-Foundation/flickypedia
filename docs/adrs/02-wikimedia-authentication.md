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

*   Flickypedia needs to act on behalf of users in WMC
    *   Can't allow anonymous uploads; too much potential for spam/vandalism
    *   Uploads should be associated with user a/c, not Flickypedia
*   Need a way to auth with WMC

## Desirable outcomes

*   Users can log in to WMC
*   Users can log out of Flickypedia and remove all access
*   Minimal perms
    *   Flickypedia only needs to upload photos and edit some metadata
    *   No need for extensive perms
*   Minimal risk of impersonation
    *   if somebody logs into Flickypedia, doesn't open door to future edits on their a/c
    *   Flickypedia shouldn't be potential point of compromise
*   Don't want to roll our own crypto etc

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
