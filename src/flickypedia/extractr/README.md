# extractr

Wikimedia Commons provides snapshots of their entire data set, in particular:

*	A complete snapshot of the structured data definitions
*	A complete snapshot of all the XML revisions

These snapshots are large and unwieldy to work with, expanding to hundreds of gigabytes of data.
Most of that is irrelevant for Flickypedia.

The `extractr` tool tries to boil those snapshots down to the bits we care about.

In particular:

*	Create a spreadsheet matching structured data statements to Flickr photos:

	```console
	$ flickypedia extractr get-photos-from-sdc [SDC_SNAPSHOT]
	```

	This command will look through the SDC statements of every file in a snapshot, and find any whose SDC suggests they come from Flickr.
	The results will be written to a spreadsheet.
