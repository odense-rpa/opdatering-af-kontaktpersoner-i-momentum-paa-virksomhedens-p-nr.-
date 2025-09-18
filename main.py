import asyncio
import logging
import sys

from automation_server_client import AutomationServer, Workqueue, WorkItemError, Credential
from momentum_client.manager import MomentumClientManager
from odk_tools.tracking import Tracker

tracker: Tracker
momentum: MomentumClientManager
proces_navn = "Opdatering af kontaktpersoner i Momentum på virksomhedens p-nummer"



async def populate_queue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from populate workqueue!")
    sagsbehandlere = momentum.virksomheder.hent_virksomheds_sagsbehandlere("4224e7fb-40c9-409c-938e-8aae62d5d753")
    kontaktpersoner = momentum.virksomheder.hent_virksomheds_kontaktpersoner("4224e7fb-40c9-409c-938e-8aae62d5d753")
    
    # Tag listen af kontaktpersoner ud af responsen
    if isinstance(kontaktpersoner, dict) and 'data' in kontaktpersoner:
        kontaktpersoner_list = kontaktpersoner['data']
    else:
        kontaktpersoner_list = []
    
    # Fjern alle kontaktpersoner der er sagsbehandlere - det er med contactRoleCode '057CBDC6-155E-45F8-BE9A-6E10A7C63906'
    filtered_kontaktpersoner = [
        k for k in kontaktpersoner_list 
        if isinstance(k, dict) and k.get('contactRoleCode') != "057CBDC6-155E-45F8-BE9A-6E10A7C63906"
    ]

    # Loop alle filterede kontaktpersoner og check om displayName også findes i sagsbehandlere
    for kontaktperson in filtered_kontaktpersoner:
        if isinstance(kontaktperson, dict):
            display_name = kontaktperson.get('displayName')
            if display_name and any(isinstance(s, dict) and s.get('displayName') == display_name for s in sagsbehandlere["data"]):
                logger.info(f"Kontaktperson {display_name} er også sagsbehandler, springer over.")
                continue  # Spring denne kontaktperson over

            # Tilføj kontaktpersonen til workqueue
            data = {
                "Navn": display_name,
                "Id": kontaktperson.get('id'),
            }
            workqueue.add_item(data=data, reference=display_name)


async def process_workqueue(workqueue: Workqueue):
    logger = logging.getLogger(__name__)

    logger.info("Hello from process workqueue!")

    for item in workqueue:
        with item:
            data = item.data  # Item data deserialized from json as dict
 
            try:
                logger.info(f"Processing kontaktperson: {data.get('Navn')} (ID: {data.get('Id')})")
                
                inaktiver_medarbejder = momentum.virksomheder.ændr_kontaktpersons_status(
                    kontaktpersonId=str(data["Id"]), status=False
                )
                
                if inaktiver_medarbejder:
                    logger.info(f"Successfully deactivated kontaktperson: {data.get('Navn')}")
                    tracker.track_task(process_name=proces_navn)
                else:
                    logger.warning(f"Failed to deactivate kontaktperson: {data.get('Navn')}")
                    
            except Exception as e:
                logger.error(f"Unexpected error processing item: {data}. Error: {e}")
                raise  # Re-raise as WorkItemError will be caught by outer except
            except WorkItemError as e:
                # A WorkItemError represents a soft error that indicates the item should be passed to manual processing or a business logic fault
                logger.error(f"Error processing item: {data}. Error: {e}")
                item.fail(str(e))


if __name__ == "__main__":
    ats = AutomationServer.from_environment()

    workqueue = ats.workqueue()

    # Initialize external systems for automation here..
    tracking_credential = Credential.get_credential("Odense SQL Server")
    tracker = Tracker(
        username=tracking_credential.username, password=tracking_credential.password
    )
    momentum_credential = Credential.get_credential("Momentum - produktion")
    momentum = MomentumClientManager(
        base_url=momentum_credential.data["base_url"],
        client_id=momentum_credential.username,
        client_secret=momentum_credential.password,
        api_key=momentum_credential.data["api_key"],
        resource=momentum_credential.data["resource"],
    )

    # Queue management
    if "--queue" in sys.argv:
        workqueue.clear_workqueue("new")
        asyncio.run(populate_queue(workqueue))
        exit(0)

    # Process workqueue
    asyncio.run(process_workqueue(workqueue))
