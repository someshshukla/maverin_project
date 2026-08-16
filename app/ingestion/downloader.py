import os
import requests
from typing import List, Dict

SAMPLE_3GPP_SPECS: List[Dict] = [
    {
        "filename": "TS_23.501_Rel-18.txt",
        "spec_number": "23.501",
        "title": "System Architecture for the 5G System (5GS)",
        "release": "Rel-18",
        "version": "18.4.0",
        "source_url": "https://www.3gpp.org/ftp/Specs/archive/23_series/23.501/",
        "sections": [
            {
                "section": "5.1",
                "section_title": "General Concepts and Architecture Principles",
                "page": 12,
                "content": """The 5G System architecture is defined as service-based and data-centric. The architecture supports data connectivity and services enabling deployments to use techniques such as Network Function Virtualization (NFV) and Software Defined Networking (SDN). The 5G system architecture consists of network functions (NFs) such as AMF, SMF, UPF, PCF, UDM, and AUSF."""
            },
            {
                "section": "5.3.2",
                "section_title": "Registration Management and Role of AMF",
                "page": 42,
                "content": """The Access and Mobility Management Function (AMF) includes the following key functionalities:
- Termination of RAN CP interface (N2).
- Termination of NAS (N1), NAS ciphering and integrity protection.
- Registration management, Connection management, Reachability management, Mobility Management.
- Transport for User Plane (UP) security activation between UE and RAN.
- Transport for Session Management messages between UE and SMF.
- AMF performs authorization of UE registration and authentication handling in coordination with AUSF/UDM.
During UE registration, the AMF processes the Registration Request received over N1 from the UE or forwarded over N2 by the gNB, allocates a 5G-GUTI if applicable, and manages the UE registration context."""
            },
            {
                "section": "5.6.1",
                "section_title": "Session Management and UPF Functions",
                "page": 68,
                "content": """The User Plane Function (UPF) handles user plane processing. UPF functionality includes:
- Anchor point for Intra-/Inter-RAT mobility (when applicable).
- External PDU session point of interconnect to Data Network (DN).
- Packet routing & forwarding (e.g. support of Uplink classifier to route traffic flows to an instance of a data network).
- Packet inspection and Quality of Service (QoS) handling for user plane.
- Downlink packet buffering and Downlink data notification triggering."""
            },
            {
                "section": "5.8.2",
                "section_title": "Service Based Interfaces and Network Functions",
                "page": 95,
                "content": """The 5G System relies on Service Based Interfaces (SBI) in the Control Plane. Network Functions export services via HTTP/2 and JSON REST APIs.
- Namf: Service provided by AMF.
- Nsmf: Service provided by SMF.
- Nudm: Service provided by UDM.
- Npcf: Service provided by PCF."""
            }
        ]
    },
    {
        "filename": "TS_23.502_Rel-18.txt",
        "spec_number": "23.502",
        "title": "Procedures for the 5G System (5GS)",
        "release": "Rel-18",
        "version": "18.3.0",
        "source_url": "https://www.3gpp.org/ftp/Specs/archive/23_series/23.502/",
        "sections": [
            {
                "section": "4.2.2",
                "section_title": "Registration Procedures",
                "page": 31,
                "content": """A UE registers with the 5G System to receive services, perform mobility updates, or re-establish session management.
Step 1: UE sends an AN message containing NAS Registration Request to gNB over the N1/Radio interface.
Step 2: gNB selects an AMF and forwards the NAS Registration Request over the N2 interface via N2 Initial UE Message.
Step 3: If the selected AMF has changed, the new AMF sends Namf_Communication_UEContextTransfer to the old AMF to retrieve the UE context.
Step 4: Authentication and Security checks are executed with AUSF and UDM.
Step 5: AMF sends Registration Accept message containing 5G-GUTI, Allowed NSSAI, and T3512 timer values to the UE."""
            },
            {
                "section": "4.3.2",
                "section_title": "UE Requested PDU Session Establishment",
                "page": 75,
                "content": """PDU Session Establishment allows the UE to establish a data path to a Data Network (DN).
Step 1: UE sends a NAS message containing PDU Session Establishment Request to the AMF over N1.
Step 2: AMF selects an SMF based on DNN and S-NSSAI, and invokes Nsmf_PDUSession_CreateSMContext.
Step 3: SMF authenticates session parameters, selects a UPF, establishes N4 session with UPF, and assigns an IP address to the UE.
Step 4: SMF responds to AMF, which sends N2 PDU Session Request containing N3 tunnel info to gNB."""
            }
        ]
    },
    {
        "filename": "TS_24.501_Rel-18.txt",
        "spec_number": "24.501",
        "title": "Non-Access-Stratum (NAS) protocol for 5G System (5GS)",
        "release": "Rel-18",
        "version": "18.2.0",
        "source_url": "https://www.3gpp.org/ftp/Specs/archive/24_series/24.501/",
        "sections": [
            {
                "section": "10.2.1",
                "section_title": "5GS NAS Timers - T3510 Timer",
                "page": 110,
                "content": """Timer T3510 is a 5GS NAS timer maintained at the UE side during the Registration procedure.
- Start: Started when the UE transmits a REGISTRATION REQUEST message to the network over NAS.
- Stop: Stopped when the UE receives a REGISTRATION ACCEPT or REGISTRATION REJECT message from the AMF.
- Default value: 15 seconds.
- On expiry (1st to 4th expiry): UE retransmits the REGISTRATION REQUEST message and resets timer T3510.
- On 5th expiry: UE aborts the registration procedure, resets the retry count, and enters 5GMM-DEREGISTERED.ATTEMPTING-TO-REGISTER state."""
            },
            {
                "section": "10.2.4",
                "section_title": "5GS NAS Timers - T3512 Timer",
                "page": 114,
                "content": """Timer T3512 is the Periodic Registration Update timer maintained at the UE.
- Start: Started when the UE enters 5GMM-REGISTERED state and periodic registration update is enabled.
- Stop: Stopped when the UE initiates a Registration procedure or enters 5GMM-DEREGISTERED state.
- Default value: Provided by the AMF in the REGISTRATION ACCEPT message (typically 54 minutes or up to 186 hours depending on configuration).
- On expiry: UE initiates a Periodic Registration Update procedure by sending a REGISTRATION REQUEST message."""
            }
        ]
    },
    {
        "filename": "TS_38.331_Rel-18.txt",
        "spec_number": "38.331",
        "title": "NR; Radio Resource Control (RRC) Protocol Specification",
        "release": "Rel-18",
        "version": "18.1.0",
        "source_url": "https://www.3gpp.org/ftp/Specs/archive/38_series/38.331/",
        "sections": [
            {
                "section": "5.3.3",
                "section_title": "RRC Connection Establishment",
                "page": 55,
                "content": """The RRC Connection Establishment procedure is used to establish an RRC connection between UE and gNB.
Procedure:
1. UE transitions from RRC_IDLE to RRC_CONNECTED.
2. UE sends RRCSetupRequest message on CCCH.
3. gNB responds with RRCSetup message containing dedicated radio resource configurations.
4. UE configures radio resources and transmits RRCSetupComplete message on DCCH, including piggybacked NAS Registration Request."""
            }
        ]
    },
    {
        "filename": "TS_29.502_Rel-18.txt",
        "spec_number": "29.502",
        "title": "5G System; Session Management Services; Stage 3",
        "release": "Rel-18",
        "version": "18.3.0",
        "source_url": "https://www.3gpp.org/ftp/Specs/archive/29_series/29.502/",
        "sections": [
            {
                "section": "5.2.2.2",
                "section_title": "Nsmf_PDUSession CreateSMContext Service Operation",
                "page": 35,
                "content": """The Nsmf_PDUSession_CreateSMContext service operation allows the AMF to request the SMF to create an SM context for a PDU session.
The HTTP POST method is used on the resource URI: '/nsmf-pdusession/v1/sm-contexts'.
Request payload includes:
- supi or gpsi (Subscriber identifier)
- pduSessionId
- dnn (Data Network Name)
- sNssai (Single Network Slice Selection Assistance Information)
- amfId & amfUri
- userLocation (User Location Information in 3GPP RAN)."""
            }
        ]
    }
]

def download_or_generate_dataset(output_dir: str) -> List[str]:
    """Generates clean structured text files representing 3GPP specifications."""
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []
    
    for spec in SAMPLE_3GPP_SPECS:
        filepath = os.path.join(output_dir, spec["filename"])
        content_lines = [
            f"Specification: TS {spec['spec_number']}",
            f"Title: {spec['title']}",
            f"Release: {spec['release']}",
            f"Version: {spec['version']}",
            f"Source URL: {spec['source_url']}",
            "=" * 60,
            ""
        ]
        
        for sec in spec["sections"]:
            content_lines.append(f"Chapter/Section: {sec['section']}")
            content_lines.append(f"Section Title: {sec['section_title']}")
            content_lines.append(f"Page: {sec['page']}")
            content_lines.append("-" * 40)
            content_lines.append(sec['content'])
            content_lines.append("\n")
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))
            
        generated_files.append(filepath)
        
    return generated_files

if __name__ == "__main__":
    import sys
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    files = download_or_generate_dataset(out_dir)
    print(f"Generated {len(files)} 3GPP specification files in {out_dir}")
