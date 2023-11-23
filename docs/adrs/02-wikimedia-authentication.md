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

When Flickypedia uploads a photo to Wikimedia Commons (WMC), that upload needs to be associated with a WMC user.
You can't upload without logging in to your Wikimedia account.

For users, this means they can see their uploads in their upload history.
For WMC and the Wikimedia Foundation, this avoids any risks associated with anonymous uploads – spam, vandalism, license washing, and more.

We need a way for user to authenticate with WMC, and for Flickypedia to upload photos on their behalf.

## Desirable outcomes

There are some basic functional requirements for Flickypedia to work correctly:

*   Users can log in to Flickypedia, allowing it to perform uploads on their behalf.
*   Users can easily log out, and revoke Flickypedia's access.

We also want Flickypedia to be a secure user of the Wikimedia APIs:

*   We don't want Flickypedia to be used to compromise Wikimedia user accounts.
    For example, we're going to get permission to make edits on a user's behalf – we don't want this permission to be misused to make vandal edits in their name.
*   This needs to work when Flickypedia only runs on a single instance.
    We're going to run Flickypedia on a Mac Mini server in our London office, so we can't e.g. rely on the existence of some external "secure database" which is separate from the web server.
*   We only have a single developer, and no dedicated security team, so we need to keep it simple.
    That means no rolling our own crypto, inventing new token schemes, or other "clever ideas" – we should stick to existing approaches.

## Decisions

### How do we authenticate users with the Wikimedia APIs?

The [Wikimedia API docs][wikimedia_auth] describe our exact use case for authentication:

> To allow your app to interact with and access content on behalf of a user, use the OAuth 2.0 authorization code flow.
> This provides a secure process for users to log in with their Wikimedia account and authorize your app.
> The OAuth 2.0 authorization code workflow can be used by server-side, client-side, and installed apps.

This is a pretty standard pattern for authentication on the web, and one that I've used before.
There are plenty of guides for implementing OAuth 2.0 in a secure way.

**We're going to use OAuth 2.0 with the authorization code flow.**
I also discussed this with some devs at the Wikimedia Foundation, who agreed that this is the right approach to use.

Alternatives considered:

*   OAuth 1.0a: The underlying MediaWiki software [also supports OAuth 1.0a][mediawiki_oauth] (this is what Flickr2Commons uses).
    That works, but the recommendation is to use OAuth 2.0, and I don't know any compelling reasons to use OAuth 1.0a in this case.
*   OAuth 2.0, with the [client credentials flow][client_credentials].
    This is for authenticating on behalf of an app, which means all the uploads would be associated with Flickypedia rather than individual users.
    That's not what we want.
*   OAuth 2.0, with [personal API tokens][api_tokens].
    These tokens are useful for testing, but we can't ask users to give us their tokens – sharing tokens is explicitly forbidden in the Wikimedia API docs.

[mediawiki_oauth]: https://www.mediawiki.org/wiki/OAuth/For_Developers
[wikimedia_auth]: https://api.wikimedia.org/wiki/Authentication
[client_credentials]: https://api.wikimedia.org/wiki/Authentication#App_authentication
[api_tokens]: https://api.wikimedia.org/wiki/Authentication#Personal_API_tokens

### Where do we call the Wikimedia APIs?

There are two options:

*   We could have our Python server call the Wikimedia APIs, or
*   We could have JavaScript in the user's browser call the Wikimedia APIs

**We're going to call the Wikimedia APIs from our Python server, not from the user's browser.**
This gives us a couple of benefits:

*   We have a much better setup for testing and managing our Python code.
    Making the Wikimedia API calls in Python means we're more likely to get that code right, and we'll have more visibility when it goes wrong.
*   It means Flickypedia can work without JavaScript in the user's browser.

This could become an issue if Flickypedia is used to upload lots of photos, because then our web server becomes a bottleneck – but I doubt we'll be reaching that level of scale any time soon.

### How do we implement OAuth 2.0 in Python?

The [Wikimedia authentication docs][wikimedia_auth] describe how the Wikimedia OAuth flow works; it's a pretty standard pattern.
We need some code to manage the flow, e.g. fetching and refreshing tokens.

**We're going to use the [Authlib library][authlib].**
This is a widely-used, well-maintained library, which has good integration with httpx, the HTTP library that we're using to call the Wikimedia API.
I'm particularly interested in its support for refresh tokens, which feel a bit fiddly.

I've read some of authlib's OAuth 2.0 code, and it looks sensible to me.
Caveat that I haven't reviewed it thoroughly and I'm not a security expert, but I could understand how e.g. it exchanges an authorization code for an access token.

Alternatives considered:

*   Writing our own implementation.
    I’m sure I could write a passable implementation of the OAuth 2.0, but "passable" isn't good enough for security-sensitive code.
    I'm more comfortable using an existing library that avoids the common mistakes and pitfalls that I might make.
*   Use the [mwoauth library][mwoauth].
    This is an OAuth library specifically for MediaWiki implementations, but as far as I can tell it only supports OAuth 1.0a, so it's not suitable for Flickypedia.
*   Use the [httpx-oauth library][httpx_oauth].
    I can't tell if this is actively maintained or widely used, so I don't want to rely on it.

[authlib]: https://authlib.org/
[mwoauth]: https://pypi.org/project/mwoauth/
[httpx_oauth]: https://frankie567.github.io/httpx-oauth/

### Where do we store the OAuth tokens?

The OAuth 2.0 authorization code flow gives us an access token that we can use to make Wikimedia edits on behalf of the user.
This is a powerful credential, that we don't want to leak!
We only want it to be used for bona fide Flickypedia edits.

There are two parts to the token:

*   An *access token*, which can be used for up to four hours to make requests against the Wikimedia API.
*   A *refresh token*, which can be used for up to a year to get new access tokens.
    Note that refresh tokens are single-use – whenever you use a refresh token to get a new access token, you also get a new refresh token which replaces the one you just used.

I considered a couple of options:

1.  Store the token in the user's session cookie.

    This is the simplest to implement in Flask, but now we're sending the token to the user's browser.
    That feels like an unnecessary risk – we're getting the access token on our server, and we're only calling the Wikimedia APIs from the same server.
    The token doesn't need to leave the server, so it shouldn't.

    Also, cookies can only have 4KB of data.
    A Wikimedia OAuth token is almost that big!

2.  Store the token in a server-side database, encrypted with a single key.

    Now there aren't any tokens in the user's browser, but this token database becomes a high-value target.
    If you could compromise that database, you get all the tokens.
    Eek!

    And because we're going to run Flickypedia on a single machine, this feels like a plausible risk – the token database and Flickypedia app will run on that machine, which means the encryption key has to live there as well.

    It wouldn't be hard for me as the sysadmin to get into that database, and that makes me uncomfortable – even if I know I'm nice and I wouldn't do anything evil, it would be better if I *couldn't*.

3.  Store the token in a server-side database, encrypted with a per-session key.

    When the user logs in, generate a random encryption key, and use that to encrypt their tokens in the server-side database.
    Store the encryption key in their session cookie.

    Whenever the user is interacting with the app, get the encryption key from their session cookie, decrypt the token in the database, do stuff on their behalf.

    This means that you need to compromise the user's browser *and* the server-side database before you get anything useful.
    Otherwise you get an encryption key or an encrypted token, and neither is useful without the other.

The final approach makes me most comfortable, because it means that the Flickypedia server isn't a single point of compromise.
If you break in and steal the token database, you get a bunch of encrypted values that you can't do anything with.

Implementation details:

*   I'm using a [recipe for Fernet encryption][fernet] in the python-cryptography library to generate the encryption keys and encrypt the tokens.
    This is another widely-used, well-tested library.
*   When a user logs out, we delete their session cookie and database entry.
*   We record the login time as part of the database entry, so we can purge entries later if we know the user's session has expired.
*   We repeatedly check that the user's OAuth token is active and valid, and log them out if not – for example, if somebody tampers with their session cookie and deletes the encryption key.

[fernet]: https://cryptography.io/en/latest/fernet/

## Future considerations

How long does user need to be logged in for?
What if we store less tokens?

## Summary

*   We're going to use OAuth 2.0 with the authorization code flow.
*   We're going to call the Wikimedia APIs from our Python server, using the [Authlib library][authlib].
