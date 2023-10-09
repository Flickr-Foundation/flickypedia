# Create an OAuth 2.0 application

Flickypedia is an OAuth 2.0 application on Wikimedia.

If you want to create new API keys (either to run your own instance of Flickypedia or for development work):

1.  Read [OAuth/For Developers][for_developers] in the MediaWiki docs.

2.  Open the Special:OAuthConsumerRegistration/propose form:

    *   [in the live Wikimedia Commons environment](https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose)
    *   [in the beta Wikimedia Commons environment](https://meta.wikimedia.beta.wmflabs.org/wiki/Special:OAuthConsumerRegistration/propose)

3.  Click "Propose an OAuth 2.0 client".

4.  Fill in the Application name, Consumer version, Application description, and so on.

    In the list of applicable grants, select the following:
    
    *   Create, edit, and move pages
    *   Upload new files

You will get a client ID and client secret.
Make sure you write these down -- you'll need them later!

[for_developers]: https://www.mediawiki.org/wiki/OAuth/For_Developers
