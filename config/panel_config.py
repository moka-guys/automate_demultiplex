#!/usr/bin/python3
""" PANEL NUMBERS AND PANEL PROPERTIES

The panel config file contains the panel numbers and panel properties, which are used by the setoff_workflows script.

The PANEL_DICT is built up in stages using various other dictionaries to reduce repetition. The base dictionary is the
DEFAULT_DICT, which is incorporated into the CAPTURE_PANEL_DICT, which are then imported into the PANEL_DICT. The
dictionaries POLYEDGE_INPUTS and CONGENICA_CREDENTIALS are also imported into the PANEL_DICT.

Panel number lists are created from the PANEL_DICT, assimilating pan numbers from the PANEL_DICT which meet the
required criteria to be included in that list.

- SNP does not have R numbers (test_number) as it is an identity check for the GMS SMS
- Panels for WES (analysed in Congenica) and TSO500 (analysed in QCII), and ArcherDX (analysed in Archer software),
    are applied at the point of analysis, so R and M numbers (test_number) for these are not listed below. These
    pan numbers do not necessarily refer to bed files but rather project configuration (e.g. DNAnexus instances,
    project layout etc.)

Dictionary keys and values are as follows. Values are None where they are not
required for analysis of samples with that pan number
    panel_name                      Name of capture panel
    pipeline                        Name of pipeline
    sample_prefix                   Expected string at front of sample name
    capture_pan_num                 Pan number of capture panel bedfile (used for RPKM). None if RPKM not run
    hsmetrics_bedfile               bedfile filename, or None
    sambamba_bedfile                bedfile filename, or None. Coverage BED
    variant_calling_bedfile         bedfile filename, or None
    FH                              True if requires PRS analysis, None if not
    rpkm_bedfile                    Bedfile filename, or None
    capture_type                    Amplicon or Hybridisation
    multiqc_coverage_level          Value
    clinical_coverage_depth         Value, or None. Used as input for sambamba
    coverage_min_basecall_qual      Value or None. Sambamba minimum base quality
    coverage_min_mapping_qual       Value or None. Sambamba minimum mapping quality
    masked_reference                projectid:fileid, or None
    test_number                     R or M number, or None if no specific number
    congenica_project               None = no upload. Number = normal. SFTP = sftp upload
    congenica_credentials           'Synnovis' or 'StG'. None = Congenica app not used
    congenica_IR_template           'priority' or 'non-priority'. None = Congenica app not used
    polyedge                        None if app not required, subdictionary containing app inputs if it is required
    ed_readcount_bedfile            None if app not required, panel readcount bedfile if required
    ed_cnvcalling_bedfile           None if app not required, R-number specific bedfile if required
    dry_lab_only                    Used to determine whether to include the TSO pan
                                    number in the duty_csv pan number list
    dry_lab                         True if required to share with dry lab, None if not
    development_run                 None if pan number is not a development pan number, else True
"""
# TODO in future do we want to swap physical paths for file IDs

TOOLS_PROJECT = "project-ByfFPz00jy1fk6PjpZ95F27J"  # 001_ToolsReferenceData
MASKED_REFERENCE = (
    f"{TOOLS_PROJECT}:file-GF84GF00QfBfzV35Gf8Qg53q"  # hs37d5_Pan4967.bwa-index.tar.gz
)
POLYEDGE_INPUTS = {  # Inputs for the polyedge DNAnexus app command
    "MSH2": {
        "gene": "MSH2",
        "chrom": 2,
        "poly_start": 47641559,
        "poly_end": 47641586,
    }
}
CONGENICA_CREDENTIALS = {
    "synnovis": {
        "congenica_credentials": "Viapath",
        "congenica_IR_template": "priority",
    },
    "stg": {
        "congenica_credentials": "STG",
        "congenica_IR_template": "non-priority",
    },
}
DEFAULT_DICT = {
    # Default dictionary upon which the panel dictionary is built -
    # values are replaced within subsequent dictionaries
    "panel_name": None,
    "pipeline": None,
    "sample_prefix": None,
    "capture_pan_num": None,
    "hsmetrics_bedfile": None,
    "sambamba_bedfile": None,
    "variant_calling_bedfile": None,
    "FH": None,
    "rpkm_bedfile": None,
    "capture_type": None,
    "multiqc_coverage_level": None,
    "clinical_coverage_depth": None,
    "coverage_min_basecall_qual": None,
    "coverage_min_mapping_qual": None,
    "masked_reference": None,
    "test_number": None,
    "congenica_project": None,
    "congenica_credentials": None,
    "congenica_IR_template": None,
    "polyedge": None,
    "ed_readcount_bedfile": None,
    "ed_cnvcalling_bedfile": None,
    "FH": None,
    "dry_lab_only": None,
    "dry_lab": None,
    "development_run": None,
}


class PanelConfig:
    """
    Variables required for import into other scripts
    """

    BEDFILE_FOLDER = f"{TOOLS_PROJECT}:/Data/BED/"
    FH_PRS_BEDFILE = f"{BEDFILE_FOLDER}Pan4909.bed"
    CAPTURE_PANEL_DICT = {
        # Dictionary containing values that apply across the capture
        "vcp1": {
            **DEFAULT_DICT,
            "panel_name": "vcp1",
            "pipeline": "pipe",
            "sample_prefix": "NGS",
            "runtype": "VCP",
            "capture_pan_num": "Pan4399",
            "hsmetrics_bedfile": f"{BEDFILE_FOLDER}Pan4397data.bed",
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan4397dataSambamba.bed",
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4398data.bed",
            "ed_readcount_bedfile": f"{BEDFILE_FOLDER}Pan5208_exomedepth.bed",
            "rpkm_bedfile": f"{BEDFILE_FOLDER}Pan4399_RPKM.bed",
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 30,
            "clinical_coverage_depth": 30,
            "coverage_min_basecall_qual": 10,
            "coverage_min_mapping_qual": 20,
        },
        "vcp2": {
            **DEFAULT_DICT,
            "panel_name": "vcp2",
            "pipeline": "pipe",
            "sample_prefix": "NGS",
            "runtype": "VCP",
            "capture_pan_num": "Pan5109",
            "hsmetrics_bedfile": f"{BEDFILE_FOLDER}Pan5123data.bed",
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan5123dataSambamba.bed",
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan5119data.bed",
            "ed_readcount_bedfile": f"{BEDFILE_FOLDER}Pan5188_exomedepth.bed",
            "rpkm_bedfile": f"{BEDFILE_FOLDER}Pan5109_RPKM.bed",
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 30,
            "clinical_coverage_depth": 30,
            "coverage_min_basecall_qual": 10,
            "coverage_min_mapping_qual": 20,
        },
        "vcp3": {
            **DEFAULT_DICT,
            "panel_name": "vcp3",
            "pipeline": "pipe",
            "sample_prefix": "NGS",
            "runtype": "VCP",
            "capture_pan_num": "Pan4362",
            "hsmetrics_bedfile": f"{BEDFILE_FOLDER}Pan4995data.bed",
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan4995dataSambamba.bed",
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4995data.bed",
            "ed_readcount_bedfile": f"{BEDFILE_FOLDER}Pan5217_exomedepth.bed",
            "rpkm_bedfile": f"{BEDFILE_FOLDER}Pan4362_RPKM.bed",
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 30,
            "clinical_coverage_depth": 30,
            "coverage_min_basecall_qual": 10,
            "coverage_min_mapping_qual": 20,
        },
        "lrpcr": {
            **DEFAULT_DICT,
            "panel_name": "lrpcr",
            "pipeline": "pipe",
            "sample_prefix": "NGS",
            "runtype": "LRPCR",
            "hsmetrics_bedfile": f"{BEDFILE_FOLDER}Pan4967_reference.bed",  # CORRECT
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan5018dataSambamba.bed",  # CORRECT
            "capture_type": "Amplicon",
            "multiqc_coverage_level": 30,
            "clinical_coverage_depth": 30,
            "coverage_min_basecall_qual": 10,
            "coverage_min_mapping_qual": 20,
            "masked_reference": MASKED_REFERENCE,
        },
        "snp": {
            **DEFAULT_DICT,
            "panel_name": "snp",
            "pipeline": "snp",
            "sample_prefix": "SNP",
            "runtype": "SNP",
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4009.bed",
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 30,
        },
        "wes": {
            **DEFAULT_DICT,
            "panel_name": "wes",
            "pipeline": "wes",
            "sample_prefix": "NGS",
            "runtype": "WES",
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan493dataSambamba.bed",
            "hsmetrics_bedfile": (
                f"{BEDFILE_FOLDER}Twist_Exome_RefSeq_CCDS_v1.2_targets.bed"
            ),
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 20,
        },
        "wes_eb": {
            **DEFAULT_DICT,
            "panel_name": "wes_eb",
            "pipeline": "wes",
            "sample_prefix": "NGS",
            "runtype": "EB",
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan493dataSambamba.bed",
            "hsmetrics_bedfile": (
                f"{BEDFILE_FOLDER}Twist_Exome_RefSeq_CCDS_v1.2_targets.bed"
            ),
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 20,
        },
        "archerdx": {
            **DEFAULT_DICT,
            "panel_name": "archerdx",
            "pipeline": "archerdx",
            "sample_prefix": "ADX",
            "runtype": "ADX",
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 30,  # We don't align for Archer
        },
        "tso500": {
            **DEFAULT_DICT,
            "panel_name": "tso500",
            "pipeline": "tso500",
            "sample_prefix": "TSO",
            "runtype": "TSO",
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan5205dataSambamba.bed",
            "capture_type": "Hybridisation",
            "clinical_coverage_depth": 100,
            "multiqc_coverage_level": 100,
            "coverage_min_basecall_qual": 25,
            "coverage_min_mapping_qual": 30,
        },
        "oncodeep": {
            **DEFAULT_DICT,
            "panel_name": "oncodeep",
            "pipeline": "oncodeep",
            "sample_prefix": "OKD",
            "runtype": "OKD",
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 30,  # We don't align for OncoDEEP
        },
    }
    PIPELINES = list(set([v["pipeline"] for k, v in CAPTURE_PANEL_DICT.items()]))
    PANEL_DICT = {
        # Dictionary containing pan number-specific settings, arranged by workflow name
        # These incorporate the capture dictionary settings and build upon them
        "Pan5180": {  # Development runs (stops warning messages)
            **DEFAULT_DICT,
            "development_run": True,
        },
        "Pan4009": {  # SNP
            **CAPTURE_PANEL_DICT["snp"],
        },
        "Pan2835": {  # TWIST WES (Synnovis)
            **CAPTURE_PANEL_DICT["wes"],
            "congenica_project": "SFTP",
        },
        "Pan4940": {  # TWIST WES for EB lab (Synnovis)
            **CAPTURE_PANEL_DICT["wes_eb"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "congenica_project": 4697,
        },
        **dict.fromkeys(
            [
                "Pan4396",  # ArcherDx (Synnovis)
                "Pan5113",  # ArcherDx (BSPS)
                "Pan5115",  # ArcherDx (Control)
            ],
            {
                **CAPTURE_PANEL_DICT["archerdx"],
            },
        ),
        "Pan5226": {  # OncoDEEP
            **CAPTURE_PANEL_DICT["oncodeep"],
        },
        "Pan5085": {  # TSO500 High throughput Synnovis. no UTRs. TERT promoter
            **CAPTURE_PANEL_DICT["tso500"],
        },
        "Pan5112": {  # TSO500 High throughput BSPS. no UTRs. TERT promoter
            **CAPTURE_PANEL_DICT["tso500"],
            "dry_lab_only": True,
            "dry_lab": True,
        },
        "Pan5114": {  # TSO500 High throughput Control. no UTRs. TERT promoter
            **CAPTURE_PANEL_DICT["tso500"],
            "dry_lab": True,
        },
        "Pan5007": {  # LRPCR R207 (Synnovis) - PMS2
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R207",
            "congenica_project": 9986,
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4767data.bed",
        },
        "Pan5008": {  # LRPCR R207 (STG) - PMS2
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R207",
            "congenica_project": 10010,
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4767data.bed",
        },
        "Pan5009": {  # LRPCR R208 (Synnovis) - CHEK2
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R208",
            "congenica_project": 9984,
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4766data.bed",
        },
        "Pan5010": {  # LRPCR R208 (STG) - CHEK2
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R208",
            "congenica_project": 10009,
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4766data.bed",
        },
        "Pan5011": {  # LRPCR R210 (Synnovis) - PMS2
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R210",
            "congenica_project": 9981,
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4767data.bed",
        },
        "Pan5012": {  # LRPCR R210 (STG) - PMS2
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R210",
            "congenica_project": 10042,
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4767data.bed",
        },
        "Pan5013": {  # LRPCR R211 (Synnovis) - PMS2
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R211",
            "congenica_project": 9982,
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4767data.bed",
        },
        "Pan5014": {  # LRPCR R211 (STG) - PMS2
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R211",
            "congenica_project": 10042,
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4767data.bed",
        },
        "Pan5015": {  # LRPCR R71 (Synnovis) - SMN1
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R71",
            "congenica_project": 9547,
            "congenica_IR_template": "non-priority",  # Overrides default priority setting for Synnovis
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4971data.bed",
        },
        "Pan5016": {  # LRPCR R239 (Synnovis) - IKBKG
            **CAPTURE_PANEL_DICT["lrpcr"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R239",
            "congenica_project": 9985,
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4768data.bed",
        },
        "Pan4119": {  # VCP1 R134 (Synnovis) - FH small panel
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R134",
            "congenica_project": 4664,
            "FH": True,
            "ed_cnvcalling_bedfile": "Pan5215",
        },
        "Pan4121": {  # VCP1 R184 (Synnovis) - Cystic Fibrosis
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R184",
            "congenica_project": 4862,
            "ed_cnvcalling_bedfile": "Pan4703",
        },
        "Pan4122": {  # VCP1 R25 (Synnovis) - FGFR. CNV not required
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R25",
            "congenica_project": 5291,
        },
        "Pan4125": {  # VCP1 R73 (Synnovis) - Duchenne or Becker muscular dystrophy
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R73",
            "congenica_project": 4861,
            "ed_cnvcalling_bedfile": "Pan4622",
        },
        "Pan4126": {  # VCP1 R337 (Synnovis) - CADASIL. CNV not required
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R337",
            "congenica_project": 4865,
        },
        "Pan4974": {  # VCP1 R112 (Synnovis) - Molecular Haemostasis Factor II deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R112",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4985",
        },
        "Pan4975": {  # VCP1 R115 (Synnovis) - Molecular Haemostasis Factor V deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R115",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4986",
        },
        "Pan4976": {  # VCP1 R116 (Synnovis) - Molecular Haemostasis Factor VII deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R116",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4987",
        },
        "Pan4977": {  # VCP1 R117 (Synnovis) - Molecular Haemostasis Factor VIII deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R117",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4988",
        },
        "Pan4978": {  # VCP1 R118 (Synnovis) - Molecular Haemostasis Factor IX deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R118",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4989",
        },
        "Pan4979": {  # VCP1 R119 (Synnovis) - Molecular Haemostasis Factor X deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R119",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4990",
        },
        "Pan4980": {  # VCP1 R120 (Synnovis) - Molecular Haemostasis Factor XI deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R120",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4991",
        },
        "Pan4981": {  # VCP1 R121 (Synnovis) - Molecular Haemostasis von Willebrand disease
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R121",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4708",
        },
        "Pan4982": {  # VCP1 R122 (Synnovis) - Molecular Haemostasis Factor XIII deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R122",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4992",
        },
        "Pan4983": {  # VCP1 R123 (Synnovis) - Molecular Haemostasis Combined vitamin
            # K-dependent clotting factor deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R123",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4993",
        },
        "Pan4984": {  # VCP1 R124 (Synnovis) - Molecular Haemostasis Combined factor V and VIII deficiency
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R124",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan4994",
        },
        "Pan4821": {  # VCP1 R134 (STG) - FH
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R134",
            "congenica_project": 4203,
            "FH": True,
            "ed_cnvcalling_bedfile": "Pan5215",
        },
        "Pan4822": {  # VCP1 R184 (STG) - CF
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R184",
            "congenica_project": 4203,
            "ed_cnvcalling_bedfile": "Pan4703",
        },
        "Pan4823": {  # VCP1 R25 (STG) - FGFR. CNV not required
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R25",
            "congenica_project": 4203,
        },
        "Pan4824": {  # VCP1 R73 (STG) - DMD
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R73",
            "congenica_project": 4203,
            "ed_cnvcalling_bedfile": "Pan4622",
        },
        "Pan4825": {  # VCP1 R337 (STG) - cadasil. CNV not required
            **CAPTURE_PANEL_DICT["vcp1"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R337",
            "congenica_project": 4203,
        },
        "Pan4149": {  # VCP2 R208 (Synnovis) - BRCA
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R208",
            "congenica_project": 4665,
            "ed_cnvcalling_bedfile": "Pan5158",
        },
        "Pan4150": {  # VCP2 R207 (Synnovis) - ovarian cancer
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R207",
            "congenica_project": 4864,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5152",
        },
        "Pan4129": {  # VCP2 R210 (Synnovis) - Inherited MMR deficiency (Lynch syndrome)
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R210",
            "congenica_project": 5094,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5206",
        },
        "Pan4964": {  # VCP2 R259 (Synnovis) - Nijmegen breakage syndrome
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R259",
            "congenica_project": 9118,
            "ed_cnvcalling_bedfile": "Pan5161",
        },
        "Pan4130": {  # VCP2 R211 (Synnovis) - Inherited polyposis and early onset colorectal cancer - germline testing
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R211",
            "congenica_project": 5095,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5193",
        },
        "Pan5121": {  # VCP2 R430 (Synnovis) - Inherited prostate cancer
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R430",
            "congenica_project": 12814,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5165",
        },
        "Pan5185": {  # VCP2 R414 (STG) - APC associated Polyposis
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R414",
            "congenica_project": 4202,
            "ed_cnvcalling_bedfile": "Pan5162",
        },
        "Pan5186": {  # VCP2 R414 (Synnovis) - APC associated Polyposis
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R414",
            "congenica_project": 5095,
            "ed_cnvcalling_bedfile": "Pan5162",
        },
        "Pan5143": {  # VCP2 R444.1 (Synnovis) - Breast cancer (PARP treatment)
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R444.1",
            "congenica_project": 14563,
            "ed_cnvcalling_bedfile": "Pan5183",
        },
        "Pan5147": {  # VCP2 R444.2 (Synnovis) - Prostate cancer (PARP treatment)
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R444.2",
            "congenica_project": 14564,
            "ed_cnvcalling_bedfile": "Pan5184",
        },
        "Pan4816": {  # VCP2 R208 (STG) - Inherited breast cancer and ovarian cancer
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R208",
            "congenica_project": 12915,
            "ed_cnvcalling_bedfile": "Pan5158",
        },
        "Pan4817": {  # VCP2 R207 (STG) - Inherited ovarian cancer (without breast cancer)
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R207",
            "congenica_project": 12914,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5152",
        },
        "Pan5122": {  # VCP2 R430 (STG) - Inherited prostate cancer
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R430",
            "congenica_project": 12913,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5165",
        },
        "Pan5144": {  # VCP2 R444.1 (STG) - Breast cancer (PARP treatment)
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R444.1",
            "congenica_project": 14629,
            "ed_cnvcalling_bedfile": "Pan5183",
        },
        "Pan5148": {  # VCP2 R444.2 (STG) - Prostate cancer (PARP treatment)
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R444.2",
            "congenica_project": 14630,
            "ed_cnvcalling_bedfile": "Pan5184",
        },
        "Pan4819": {  # VCP2 R210 (STG) - Inherited MMR deficiency (Lynch syndrome)
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R210",
            "congenica_project": 4202,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5206",
        },
        "Pan4820": {  # VCP2 R211 (STG) - Inherited polyposis and early onset colorectal cancer - germline testing
            **CAPTURE_PANEL_DICT["vcp2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R211",
            "congenica_project": 4202,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5193",
        },
        "Pan4145": {  # VCP3 R79 (Synnovis) - Congenital muscular dystrophy
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R79",
            "congenica_project": 4666,
            "ed_cnvcalling_bedfile": "Pan5220",
        },
        "Pan4146": {  # VCP3 R81 (Synnovis) - Congenital myopathy
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R81",
            "congenica_project": 4666,
            "ed_cnvcalling_bedfile": "Pan5170",
        },
        "Pan4132": {  # VCP3 R56 (Synnovis) - Adult onset dystonia, chorea or related movement disorder.
            # CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R56",
            "congenica_project": 5092,
        },
        "Pan4134": {  # VCP3 R57 (Synnovis) - Childhood onset dystonia, chorea or related movement disorder.
            # CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R57",
            "congenica_project": 5092,
        },
        "Pan4136": {  # VCP3 R58 (Synnovis) - Adult onset neurodegenerative disorder. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R58",
            "congenica_project": 5092,
        },
        "Pan4137": {  # VCP3 R60 (Synnovis) - Adult onset hereditary spastic paraplegia. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R60",
            "congenica_project": 5092,
        },
        "Pan4138": {  # VCP3 R62 (Synnovis) - Adult onset leukodystrophy. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R62",
            "congenica_project": 5092,
        },
        "Pan4143": {  # VCP3 R66 (Synnovis) - Paroxysmal central nervous system disorders
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R66",
            "congenica_project": 5092,
            "ed_cnvcalling_bedfile": "Pan5174",
        },
        "Pan4144": {  # VCP3 R78 (Synnovis) - Hereditary neuropathy or pain disorders. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R78",
            "congenica_project": 5092,
        },
        "Pan4151": {  # VCP3 R82 (Synnovis) - Limb girdle muscular dystrophies, myofibrillar
            # myopathies and distal myopathies. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R82",
            "congenica_project": 5092,
        },
        "Pan4314": {  # VCP3 R229 (Synnovis) - Confirmed Fanconi anaemia or Bloom syndrome
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R229",
            "congenica_project": 5290,
            "ed_cnvcalling_bedfile": "Pan5179",
        },
        "Pan4351": {  # VCP3 R227 (Synnovis) - Xeroderma pigmentosum, Trichothiodystrophy or Cockayne syndrome
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R227",
            "congenica_project": 5522,
            "ed_cnvcalling_bedfile": "Pan5177",
        },
        "Pan4387": {  # VCP3 R90 (Synnovis) - Bleeding and platelet disorders
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R90",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan5223",
        },
        "Pan4390": {  # VCP3 R97 (Synnovis) - Thrombophilia with a likely monogenic cause
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R97",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan5173",
        },
        "Pan4826": {  # VCP3 R56 (STG) - Adult onset dystonia, chorea or related movement disorder. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R56",
            "congenica_project": 4201,
        },
        "Pan4827": {  # VCP3 R57 (STG) - Childhood onset dystonia, chorea or related movement disorder. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R57",
            "congenica_project": 4201,
        },
        "Pan4828": {  # VCP3 R58 (STG) - Adult onset neurodegenerative disorder. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R58",
            "congenica_project": 4201,
        },
        "Pan4829": {  # VCP3 R60 (STG) - Adult onset hereditary spastic paraplegia. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R60",
            "congenica_project": 4201,
        },
        "Pan4830": {  # VCP3 R62 (STG) - Adult onset leukodystrophy. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R62",
            "congenica_project": 4201,
        },
        "Pan4831": {  # VCP3 R66 (STG) - Paroxysmal central nervous system disorders
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R66",
            "congenica_project": 4201,
            "ed_cnvcalling_bedfile": "Pan5174",
        },
        "Pan4832": {  # VCP3 R78 (STG) - Hereditary neuropathy or pain disorder. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R78",
            "congenica_project": 4201,
        },
        "Pan4833": {  # VCP3 R79 (STG) - Congenital muscular dystrophy
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R79",
            "congenica_project": 4201,
            "ed_cnvcalling_bedfile": "Pan5220",
        },
        "Pan4834": {  # VCP3 R81 (STG) - Congenital myopathy
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R81",
            "congenica_project": 4201,
            "ed_cnvcalling_bedfile": "Pan5170",
        },
        "Pan4835": {  # VCP3 R82 (STG) - Limb girdle muscular dystrophies, myofibrillar myopathies
            # and distal myopathies. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R82",
            "congenica_project": 4201,
        },
        "Pan4836": {  # VCP3 R229 (STG) - Confirmed Fanconi anaemia or Bloom syndrome. CNV not required
            **CAPTURE_PANEL_DICT["vcp3"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R229",
            "congenica_project": 4201,
            "ed_cnvcalling_bedfile": "Pan5179",
        },
    }
    # ================ PAN NUMBER LISTS ===================================================
    PANELS = list(PANEL_DICT.keys())  # All panel pan numbers
    VCP_PANELS = {  # Custom Panels per-capture panel numbers
        "vcp1": [k for k, v in PANEL_DICT.items() if v["panel_name"] == "vcp1"],
        "vcp2": [k for k, v in PANEL_DICT.items() if v["panel_name"] == "vcp2"],
        "vcp3": [k for k, v in PANEL_DICT.items() if v["panel_name"] == "vcp3"],
    }
    ED_PANNOS = {
        "vcp1": [
            k
            for k, v in PANEL_DICT.items()
            if v["panel_name"] == "vcp1" and v["ed_cnvcalling_bedfile"]
        ],
        "vcp2": [
            k
            for k, v in PANEL_DICT.items()
            if v["panel_name"] == "vcp2" and v["ed_cnvcalling_bedfile"]
        ],
        "vcp3": [
            k
            for k, v in PANEL_DICT.items()
            if v["panel_name"] == "vcp3" and v["ed_cnvcalling_bedfile"]
        ],
    }
    LIBRARY_PREP_NAMES = list(
        set([v["sample_prefix"] for k, v in CAPTURE_PANEL_DICT.items()])
    )
    TSO_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "tso500"]
    WES_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "wes"]
    SNP_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "snp"]
    ARCHER_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "archerdx"]
    ONCODEEP_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "oncodeep"]
    LRPCR_PANELS = [k for k, v in PANEL_DICT.items() if v["panel_name"] == "lrpcr"]
    DEVELOPMENT_PANEL = "".join(
        [k for k, v in PANEL_DICT.items() if v["development_run"]]
    )

    # ================ DUTY_CSV INPUTS ===================================================

    # tso_pannumbers should not include the dry lab pan number as we do not want to include
    # this as input to duty_csv as we do not want to download this to the trust network
    TSO_SYNNOVIS_PANNUMBERS = [
        k
        for k, v in PANEL_DICT.items()
        if v["pipeline"] == "tso500"
        if v["dry_lab_only"] is not True
    ]
    STG_PANNUMBERS = [
        k
        for k, v in PANEL_DICT.items()
        if v["pipeline"] == "pipe" and v["congenica_credentials"] == "STG"
    ]
    CP_CAPTURE_PANNOS = [
        CAPTURE_PANEL_DICT["vcp1"]["capture_pan_num"],
        CAPTURE_PANEL_DICT["vcp2"]["capture_pan_num"],
        CAPTURE_PANEL_DICT["vcp3"]["capture_pan_num"],
    ]
