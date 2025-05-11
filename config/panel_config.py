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
- Development runs have two options for pan numbers, one for runs that require standard processing with bcl2fastq
    and one for runs that require manual processing as they have UMIs

Dictionary keys and values are as follows. Values are None where they are not
required for analysis of samples with that pan number
    panel_name                      Name of capture panel
    pipeline                        Name of pipeline
    runtype                         Type of run
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
    ed_bam_str                      String used to search for appropriate BAM
    ed_samplename_str               String used to find sample name
    dry_lab_only                    Used to determine whether to include the TSO pan
                                    number in the duty_csv pan number list
    dry_lab                         True if required to share with dry lab, None if not
    umis                            True if run has UMIs
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
    "runtype": None,
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
    "ed_bam_str": None,
    "ed_samplename_str": None,
    "dry_lab_only": None,
    "dry_lab": None,
    "umis": None,
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
            "pipeline": "gatk_pipe",
            "sample_prefix": "NGS",
            "runtype": "VCP",
            "capture_pan_num": "Pan4399",
            "hsmetrics_bedfile": f"{BEDFILE_FOLDER}Pan4397data.bed",
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan4397dataSambamba.bed",
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan4398data.bed",
            "ed_readcount_bedfile": f"{BEDFILE_FOLDER}Pan5208_exomedepth.bed",
            "readcount_ed_bam_str": "*001.ba*",
            "ed_bam_str": "001",
            "ed_samplename_str": "R1_001.bam",
            "rpkm_bedfile": f"{BEDFILE_FOLDER}Pan4399_RPKM.bed",
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 30,
            "clinical_coverage_depth": 30,
            "coverage_min_basecall_qual": 10,
            "coverage_min_mapping_qual": 20,
        },
        "CP2": {
            **DEFAULT_DICT,
            "panel_name": "CP2",
            "pipeline": "seglh_pipe",
            "sample_prefix": "NGS",
            "runtype": "CP2",
            "capture_pan_num": "Pan5272",
            "hsmetrics_bedfile": f"{BEDFILE_FOLDER}Pan5272_data.bed",
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan5272_sambamba.bed",
            "variant_calling_bedfile": f"{BEDFILE_FOLDER}Pan5272_data.bed",
            "ed_readcount_bedfile": f"{BEDFILE_FOLDER}Pan5279_exomeDepth.bed",
            "happy_bedfile": f"{BEDFILE_FOLDER}Pan5272_data.bed",
            "readcount_ed_bam_str": "*markdup.ba*",
            "ed_bam_str": "markdup",
            "ed_samplename_str": "_markdup.bam",           
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 30,
            "clinical_coverage_depth": 30,
            "coverage_min_basecall_qual": 10,
            "coverage_min_mapping_qual": 20,
        },
        "lrpcr": {
            **DEFAULT_DICT,
            "panel_name": "lrpcr",
            "pipeline": "gatk_pipe",
            "sample_prefix": "NGS",
            "runtype": "LRPCR",
            "hsmetrics_bedfile": f"{BEDFILE_FOLDER}Pan4967_reference.bed",
            "sambamba_bedfile": f"{BEDFILE_FOLDER}Pan5018dataSambamba.bed",
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
        "msk": {
            **DEFAULT_DICT,
            "panel_name": "msk",
            "pipeline": "msk",
            "sample_prefix": "MSK",
            "runtype": "MSK",
            "capture_type": "Hybridisation",
            "multiqc_coverage_level": 30,  # We don't align for MSK
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
        "dev": {
            **DEFAULT_DICT,
            "pipeline": "dev",
            "panel_name": "dev",
            "runtype": "DEV",
            "multiqc_coverage_level": 30,
        },
    }
    PIPELINES = list(set([v["pipeline"] for k, v in CAPTURE_PANEL_DICT.items()]))
    PANEL_DICT = {
        # Dictionary containing pan number-specific settings, arranged by workflow name
        # These incorporate the capture dictionary settings and build upon them
        "Pan5180": {  # Development runs (stops warning messages)
            **CAPTURE_PANEL_DICT["dev"],
        },
        "Pan5227": {  # Development run with UMIs (stops warning messages)
            **CAPTURE_PANEL_DICT["dev"],
            "umis": True,
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
        "Pan5236": {  # MSK
            **CAPTURE_PANEL_DICT["msk"],
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
        "Pan4149": {  # CP2 R208 (Synnovis) - BRCA
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R208",
            "congenica_project": 4665,
            "ed_cnvcalling_bedfile": "Pan5249",
        },
        "Pan4150": {  # CP2 R207 (Synnovis) - ovarian cancer
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R207",
            "congenica_project": 4864,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5250",
        },
        "Pan4129": {  # CP2 R210 (Synnovis) - Inherited MMR deficiency (Lynch syndrome)
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R210",
            "congenica_project": 5094,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5248",
        },
        "Pan4964": {  # CP2 R259 (Synnovis) - Nijmegen breakage syndrome
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R259",
            "congenica_project": 9118,
            "ed_cnvcalling_bedfile": "Pan5244",
        },
        "Pan4130": {  # CP2 R211 (Synnovis) - Inherited polyposis and early onset colorectal cancer - germline testing
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R211",
            "congenica_project": 5095,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5247",
        },
        "Pan5121": {  # CP2 R430 (Synnovis) - Inherited prostate cancer
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R430",
            "congenica_project": 12814,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5242",
        },
        "Pan5185": {  # CP2 R414 (STG) - APC associated Polyposis
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R414",
            "congenica_project": 4202,
            "ed_cnvcalling_bedfile": "Pan5243",
        },
        "Pan5186": {  # CP2 R414 (Synnovis) - APC associated Polyposis
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R414",
            "congenica_project": 5095,
            "ed_cnvcalling_bedfile": "Pan5243",
        },
        "Pan5143": {  # CP2 R444.1 (Synnovis) - Breast cancer (PARP treatment)
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R444.1",
            "congenica_project": 14563,
            "ed_cnvcalling_bedfile": "Pan5269",
        },
        "Pan5147": {  # CP2 R444.2 (Synnovis) - Prostate cancer (PARP treatment)
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R444.2",
            "congenica_project": 14564,
            "ed_cnvcalling_bedfile": "Pan5256",
        },
        "Pan4816": {  # CP2 R208 (STG) - Inherited breast cancer and ovarian cancer
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R208",
            "congenica_project": 18064,
            "ed_cnvcalling_bedfile": "Pan5249",
        },
        "Pan4817": {  # CP2 R207 (STG) - Inherited ovarian cancer (without breast cancer)
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R207",
            "congenica_project": 18063,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5250",
        },
        "Pan5122": {  # CP2 R430 (STG) - Inherited prostate cancer
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R430",
            "congenica_project": 18067,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5242",
        },
        "Pan5144": {  # CP2 R444.1 (STG) - Breast cancer (PARP treatment)
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R444.1",
            "congenica_project": 18068,
            "ed_cnvcalling_bedfile": "Pan5269",
        },
        "Pan5148": {  # CP2 R444.2 (STG) - Prostate cancer (PARP treatment)
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R444.2",
            "congenica_project": 18069,
            "ed_cnvcalling_bedfile": "Pan5256",
        },
        "Pan4819": {  # CP2 R210 (STG) - Inherited MMR deficiency (Lynch syndrome)
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R210",
            "congenica_project": 18065,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5248",
        },
        "Pan4820": {  # CP2 R211 (STG) - Inherited polyposis and early onset colorectal cancer - germline testing
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R211",
            "congenica_project": 18066,
            "polyedge": POLYEDGE_INPUTS["MSH2"],
            "ed_cnvcalling_bedfile": "Pan5247",
        },
        "Pan4145": {  # CP2 R79 (Synnovis) - Congenital muscular dystrophy
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R79",
            "congenica_project": 4666,
            "ed_cnvcalling_bedfile": "Pan5281",
        },
        "Pan4146": {  # CP2 R81 (Synnovis) - Congenital myopathy
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R81",
            "congenica_project": 4666,
            "ed_cnvcalling_bedfile": "Pan5273",
        },
        "Pan4143": {  # CP2 R66 (Synnovis) - Paroxysmal central nervous system disorders
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R66",
            "congenica_project": 5092,
            "ed_cnvcalling_bedfile": "Pan5240",
        },
        "Pan4314": {  # CP2 R229 (Synnovis) - Confirmed Fanconi anaemia or Bloom syndrome
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R229",
            "congenica_project": 5290,
            "ed_cnvcalling_bedfile": "Pan5245",
        },
        "Pan4351": {  # CP2 R227 (Synnovis) - Xeroderma pigmentosum, Trichothiodystrophy or Cockayne syndrome
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R227",
            "congenica_project": 5522,
            "ed_cnvcalling_bedfile": "Pan5246",
        },
        "Pan4387": {  # CP2 R90 (Synnovis) - Bleeding and platelet disorders
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R90",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan5252",
        },
        "Pan4390": {  # CP2 R97 (Synnovis) - Thrombophilia with a likely monogenic cause
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R97",
            "congenica_project": 4699,
            "ed_cnvcalling_bedfile": "Pan5251",
        },
        "Pan4831": {  # CP2 R66 (STG) - Paroxysmal central nervous system disorders
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R66",
            "congenica_project": 18061,
            "ed_cnvcalling_bedfile": "Pan5240",
        },
        "Pan4833": {  # CP2 R79 (STG) - Congenital muscular dystrophy
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R79",
            "congenica_project": 4201,
            "ed_cnvcalling_bedfile": "Pan5281",
        },
        "Pan4834": {  # CP2 R81 (STG) - Congenital myopathy
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R81",
            "congenica_project": 4201,
            "ed_cnvcalling_bedfile": "Pan5273",
        },
        "Pan4836": {  # CP2 R229 (STG) - Confirmed Fanconi anaemia or Bloom syndrome. CNV not required
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["stg"],
            "test_number": "R229",
            "congenica_project": 4201,
            "ed_cnvcalling_bedfile": "Pan5245",
        },
          "Pan5284": {  # CP2 R163 (Synnovis) - Ectodermal dysplasia
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R163",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5268",
        },
          "Pan5285": {  # CP2 R164 (Synnovis) - Epidermolysis bullosa and congenital skin fragility
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R164",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5267",
        },
          "Pan5286": {  # CP2 R165 (Synnovis) - Ichthyosis and erythrokeratoderma
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R165",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5266",
        },
          "Pan5287": {  # CP2 R166 (Synnovis) - Palmoplantar keratodermas
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R166",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5265",
        },
          "Pan5282": {  # CP2 R167 (Synnovis) - Autosomal recessive primary hypertrophic osteoarthropathy
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R167",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5264",
        },
          "Pan5283": {  # CP2 R230 (Synnovis) - Multiple monogenic benign skin tumours
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R230",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5263",
        },
          "Pan5288": {  # CP2 R236 (Synnovis) - Pigmentary skin disorders
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R236",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5262",
        },
          "Pan5293": {  # CP2 R237 (Synnovis) - Cutaneous photosensitivity with a likely genetic cause
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R237",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5261",
        },
          "Pan5292": {  # CP2 R255 (Synnovis) - Epidermodysplasia verruciformis
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R255",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5260",
        },
          "Pan5289": {  # CP2 R326 (Synnovis) - Vascular skin disorders
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R326",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5259",
        },
          "Pan5290": {  # CP2 R332 (Synnovis) - Rare genetic inflammatory skin disorders
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R332",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5258",
        },
          "Pan5291": {  # CP2 R424 (Synnovis) - Subcutaneous panniculitis T-cell lymphoma (SPTCL)
            **CAPTURE_PANEL_DICT["CP2"],
            **CONGENICA_CREDENTIALS["synnovis"],
            "test_number": "R424",
            "congenica_project": 17995,
            "ed_cnvcalling_bedfile": "Pan5257",
        },
    }
    # ================ PAN NUMBER LISTS ===================================================
    PANELS = list(PANEL_DICT.keys())  # All panel pan numbers
    VCP_PANELS = {  # Custom Panels per-capture panel numbers
        "vcp1": [k for k, v in PANEL_DICT.items() if v["panel_name"] == "vcp1"],
        "CP2": [k for k, v in PANEL_DICT.items() if v["panel_name"] == "CP2"],
    }
    ED_PANNOS = {
        "vcp1": [
            k
            for k, v in PANEL_DICT.items()
            if v["panel_name"] == "vcp1" and v["ed_cnvcalling_bedfile"]
        ],
        "CP2": [
            k
            for k, v in PANEL_DICT.items()
            if v["panel_name"] == "CP2" and v["ed_cnvcalling_bedfile"]
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
    MSK_PANELS = [k for k, v in PANEL_DICT.items() if v["pipeline"] == "msk"]
    LRPCR_PANELS = [k for k, v in PANEL_DICT.items() if v["panel_name"] == "lrpcr"]
    DEV_PANEL = [k for k, v in PANEL_DICT.items() if v["runtype"] == "dev"]
    UMI_DEV_PANEL = [k for k, v in PANEL_DICT.items() if v["umis"] == True]
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
    if v.get("pipeline", "").strip() in ("gatk_pipe", "seglh_pipe")
    and v.get("congenica_credentials", "").strip() == "STG"
]
    CP_CAPTURE_PANNOS = [
        CAPTURE_PANEL_DICT["vcp1"]["capture_pan_num"],
        CAPTURE_PANEL_DICT["CP2"]["capture_pan_num"],
    ]
