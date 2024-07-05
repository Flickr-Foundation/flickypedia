from .base import WikimediaApiBase


class IsDeletedMethod(WikimediaApiBase):
    # The format of the XML response is:
    #
    #     <?xml version="1.0"?>
    #     <api batchcomplete="">
    #       <query>
    #         <logevents>
    #           <item logid="355945145" ns="6" title="File:Mugeni Elijah.jpg" pageid="0" logpage="128511537" type="delete" action="delete" user="Minorax" timestamp="2024-06-26T02:06:08Z" comment="per [[Commons:Deletion requests/Files found with 154165274@N03]]">
    #             <params/>
    #           </item>
    #           <item logid="335508303" ns="6" title="File:Mugeni Elijah.jpg" pageid="0" logpage="115072643" type="delete" action="delete" user="Krd" timestamp="2023-02-07T04:06:55Z" comment="No permission since 30 January 2023">
    #             <params/>
    #           </item>
    #         </logevents>
    #       </query>
    #     </api>
    #
    # This uses the logevents API.
    # See https://www.mediawiki.org/wiki/API:Logevents

    def is_deleted(self, *, filename: str) -> bool:
        """
        Returns True if a file with this name has been deleted from
        Wikimedia Commons, false otherwise.
        """
        assert filename.startswith("File:")

        xml = self._get_xml(
            params={
                "action": "query",
                "list": "logevents",
                "letitle": filename,
                "letype": "delete",
            }
        )

        return len(xml.findall(".//logevents/item")) > 0
