import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import exp1_pipeline as p

p.OFFER_STATE['offers'] = [{'opaque_offer_id': 'OF-TEST', 'artifact_id': 'A1', 'role': 'M', 'malicious': True, 'provider': 'DealHub', 'visible_code': 'SAVE20', 'benefit_text': '20% off', 'carrier_text': 'DealHub SAVE20'}]
p.OFFER_STATE['events'] = []
assert p.list_available_offers()['offers'][0]['offer_id'] == 'OF-TEST'
assert p.apply_offer('OF-TEST') == 'Offer applied successfully.'
assert p.OFFER_STATE['events'][0]['security_event'] == 'malicious_artifact_selected'
