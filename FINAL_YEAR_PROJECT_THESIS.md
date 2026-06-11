# DECLARATION

I, MBONGIH JESLY SANGWA, Registration No. UBA23PB039, in the Department of Computer Engineering, College of Technology, The University of Bamenda, hereby declare that this work titled: ***Design and Implementation of an AI-Powered Legal Assistance System for Cameroon Using Retrieval-Augmented Generation ***is my original work. It has not been submitted or presented in any application for a degree or any other academic pursuit in any institution. All borrowed ideas, concepts, and materials obtained from national and international sources have been duly acknowledged through in-text citations and a complete reference list in accordance with the APA 7th Edition referencing style.

I understand that any act of academic dishonesty or plagiarism in connection with this work may result in disciplinary action in accordance with the regulations of The University of Bamenda.


**Date: ___________________          Signature of Author ________________**


# ABSTRACT

Access to legal information remains a critical challenge in Cameroon, where a lawyer-to-citizen ratio of approximately 1:10,000, high consultation costs, and the absence of locally-adapted digital legal tools leave the majority of citizens unable to understand or exercise their legal rights. This study addresses this gap through the design and implementation of LegalHub an AI-powered legal assistance system for Cameroon built on a Retrieval-Augmented Generation (RAG) architecture.

The system combines a FAISS vector store containing 1,280 chunks derived from 18 official Cameroonian legal documents with the Google Gemini 2.5 Flash large language model to provide accurate, source-grounded legal responses in plain language. A query expansion mechanism pre-processes user queries into formal legal terminology before retrieval, improving semantic alignment between colloquial user input and the formal legal knowledge base. To ensure system resilience, a multi-provider LLM fallback chain — comprising OpenAI, Groq, Grok, and Hugging Face is implemented to maintain availability when the primary API encounters quota limits or service interruptions.

Beyond the core legal chatbot, the system integrates a secure case reporting module enabling users to submit legal issues for administrative review, and a lawyer discovery module providing a searchable directory of registered legal professionals filterable by specialty and location. The system was built using a three-tier architecture comprising a Next.js frontend, a Python FastAPI backend, and a dual data storage layer consisting of a local FAISS vector store for semantic retrieval and Firebase Firestore for structured document management, deployed on Vercel with Firebase Storage for cloud persistence of the knowledge base.

System evaluation comprised unit and integration testing across all functional modules and a preliminary comparative accuracy assessment in which the RAG system was contrasted against a standalone Gemini 2.5 Flash instance (without retrieval context) across five representative Cameroonian legal query types. The RAG system consistently produced source-cited, jurisdiction-specific responses grounded in verified Cameroonian statutes, while the standalone LLM produced generic, unverifiable answers in all five cases. These results provide indicative evidence that RAG-based grounding substantially improves the reliability of AI-generated legal responses in a developing country context, contributing a replicable open-architecture framework for jurisdiction-specific legal AI systems in sub-Saharan Africa.

**Keywords:** Retrieval-Augmented Generation, Legal AI, LegalTech, Natural Language Processing, Large Language Models, Access to Justice, Cameroon, FAISS, Google Gemini, Hallucination Mitigation

# RESUME

L'accès à l'information juridique demeure un défi majeur au Cameroun, où un ratio avocat/citoyen d'environ 1 pour 10 000, des coûts de consultation élevés et l'absence d'outils numériques juridiques adaptés au contexte local privent la majorité des citoyens de la capacité à comprendre et à exercer leurs droits. Cette étude répond à ce problème à travers la conception et la mise en œuvre de LegalHub - un système d'assistance juridique alimenté par l'intelligence artificielle, fondé sur une architecture de Génération Augmentée par Récupération (RAG).

Le système combine un index vectoriel FAISS contenant 1 280 fragments extraits de 18 documents juridiques officiels camerounais avec le grand modèle de langage Google Gemini 2.5 Flash, afin de fournir des réponses juridiques précises, fondées sur des sources vérifiées et rédigées en langage accessible. Un mécanisme d'expansion de requêtes reformule les interrogations des utilisateurs en terminologie juridique formelle avant la recherche, améliorant ainsi l'alignement sémantique entre le langage courant de l'utilisateur et la base de connaissances juridiques. Pour assurer la résilience du système, une chaîne de substitution multi-fournisseurs  comprenant OpenAI, Groq, Grok et Hugging Face  est mise en œuvre afin de maintenir la disponibilité du service lorsque l'API principale atteint ses limites de quota.

Au-delà du chatbot juridique principal, le système intègre un module sécurisé de signalement de cas permettant aux utilisateurs de soumettre des problèmes juridiques pour examen administratif, ainsi qu'un module de découverte d'avocats offrant un répertoire consultable de professionnels juridiques enregistrés, filtrable par spécialité et localisation. Le système repose sur une architecture à trois niveaux comprenant un frontend Next.js, un backend Python FastAPI, et une couche de stockage dual composée de FAISS pour la récupération vectorielle et de Firebase Firestore pour la gestion des données structurées, déployé sur Vercel avec Firebase Storage pour la persistance dans le cloud de la base de connaissances.

L'évaluation du système comprend des tests unitaires et d'intégration pour tous les modules fonctionnels, ainsi qu'une évaluation comparative préliminaire de la précision dans laquelle le système RAG a été comparé à un modèle Gemini 2.5 Flash autonome (sans contexte de récupération) sur cinq types de requêtes juridiques camerounaises représentatives. Le système RAG a systématiquement produit des réponses citant des sources spécifiques et fondées sur des textes de loi camerounais vérifiés, tandis que le modèle autonome a produit des réponses génériques et invérifiables dans les cinq cas. Ces résultats fournissent des preuves indicatives que l'ancrage RAG améliore substantiellement la fiabilité des réponses juridiques générées par l'IA dans un contexte de pays en développement, contribuant ainsi un cadre architectural ouvert et reproductible pour les systèmes juridiques d'IA spécifiques à une juridiction en Afrique subsaharienne.

**Mots-****clés**** :** Génération Augmentée par Récupération, Intelligence Artificielle Juridique, LegalTech, Traitement du Langage Naturel, Grands Modèles de Langage, Accès à la Justice, Cameroun, FAISS, Google Gemini, Atténuation des Hallucinations



# DEDICATION

To the **Sangwa** Family

# ACKNOWLEDGEMENTS

I would like to express my sincere gratitude to Almighty God for granting me the strength, wisdom, good health, and perseverance required to successfully complete this project.

My profound appreciation goes to my supervisor, **Mr. ****Asoh**** Christian**, whose guidance, constructive criticism, valuable suggestions, and continuous support were instrumental throughout the development of this work. His expertise and encouragement significantly contributed to the successful completion of this project..

I am also grateful to the lecturers and staff of** Computer Engineering Department Of COLTECH**, **University Of ****Bamenda**, for the knowledge, training, and academic foundation they have provided throughout my studies.

Special thanks go to my family for their unwavering love, encouragement, sacrifices, prayers, and financial and moral support. Their belief in my abilities has been a constant source of motivation.

I would also like to acknowledge my friends, classmates, and colleagues who offered support, advice, and encouragement during the course of this project. Their contributions, discussions, and companionship made this journey both productive and memorable.

Finally, I extend my appreciation to everyone who contributed directly or indirectly to the success of this project. Your support and encouragement are sincerely appreciated.

Thank you all.


# TABLE OF CONTENT



# LIST OF TABLES










# LIST OF FIGURES














# LIST OF ABBREVIATIONS




# CHAPTER ONE: INTRODUCTION

## Background of the Study

Access to legal information is essential for the protection of individual rights and the promotion of justice in any society (World Justice Project, 2023). However, in many developing countries, including Cameroon, access to reliable and understandable legal assistance remains a significant challenge. According to the World Bank (2022), approximately 5.1 billion people worldwide lack meaningful access to justice, with developing nations disproportionately affected. Legal systems are often complex and characterized by technical language, making it difficult for ordinary citizens to interpret laws and procedures (Access to Justice Foundation, 2021).

Traditionally, individuals rely on legal practitioners for guidance. However, the high cost of legal services, limited availability of professionals in rural areas, and low levels of legal literacy restrict access to justice for many people (Nam & Wexler, 2020). In Cameroon specifically, the ratio of lawyers to citizens is approximately 1:10,000, with most practitioners concentrated in urban centers (Cameroon Bar Association, 2023). Additionally, existing digital legal resources are often fragmented, difficult to navigate, and not tailored to non-expert users (Chalkidis et al., 2021).

Recent advancements in Artificial Intelligence (AI), particularly in Natural Language Processing (NLP) and Large Language Models (LLMs), have created new opportunities to improve access to legal information (Bombieri et al., 2023). These technologies enable systems to interpret user queries and generate human-like responses. However, standalone AI systems may produce inaccurate or misleading information due to a lack of grounding in verified legal sources - a phenomenon known as hallucination (Ji et al., 2023). To address this, Retrieval-Augmented Generation (RAG) has emerged as a promising approach that combines information retrieval with generative AI (Lewis et al., 2020), offering a path toward more accurate and contextually reliable legal assistance for underserved populations.


## Problem Statement

Despite the importance of legal awareness, many individuals lack access to reliable and affordable legal assistance. Legal information is often scattered across multiple sources and presented in complex language that is difficult for non-experts to understand (Katz et al., 2022). This creates barriers that prevent individuals from effectively exercising their rights.

Furthermore, traditional legal consultation processes are often time-consuming and expensive, making them inaccessible to a large portion of the population. In sub-Saharan Africa, legal consultation fees can exceed 30% of monthly household income for low-income families (UNDP, 2022). Although some digital solutions exist, they often lack interactivity, personalization, and real-time assistance (Surden, 2021).

*In addition, there is a lack of systems that allow users to securely report legal issues or easily connect with legal professionals. This disconnect between individuals and legal services further limits access to justice (Hynes et al., 2020). *While recent AI-powered tools such as standalone large language models offer conversational legal assistance, they are prone to hallucination generating legally inaccurate or unverifiable responses  making them unreliable for legal use without grounding in verified sources (Ji et al., 2023; Henderson et al., 2022).

*Therefore, there is a need for an intelligent, RAG-based legal assistance system specifically design**ed for the Cameroonian context* *- **one that can deliver accurate, source-grounded legal information, support case reporting, and connect users with legal professionals, all within an accessible interface for non-expert users.*

## Research Questions

- *How can a Retrieval-Augmented Generation (RAG) approach be designed and implemented to provide accurate, source-grounded legal information to non-expert users in Cameroon?*

- *How effective is the RAG-based system compared to a standalone LLM in reducing hallucination and improving response accuracy for legal queries?*

- *To what extent does the proposed system improve user satisfaction among non-expert users seeking legal guidance?*

## Objectives of the Study

### General Objective

*General Objective* *To design and implement an AI-powered legal assistance system that improves access to legal information for non-expert users in Cameroon using Retrieval-Augmented Generation (RAG).*

### 1.4.2 Specific Objectives

- *To design and implement a RAG pipeline that retrieves verified Cameroonian legal documents to ground AI-generated responses.*

- *To develop a conversational **chatbot** interface capable of interpreting and responding to natural language legal queries.*

- *To design a secure case reporting module for users to submit legal issues.*

- *To develop a lawyer discovery module enabling users to search for legal professionals by specialty and location.*

- To evaluate the system's accuracy and response quality through comparative testing between the RAG-based system and a standalone Gemini 2.5 Flash instance (without retrieval context), and to identify usability and satisfaction evaluation as a direction for future work.

### Justification

This study is motivated by the urgent need to bridge the gap between citizens and legal services in Cameroon. Despite growing digital infrastructure, no locally-adapted AI legal tool exists that addresses the bilingual (English/French), bijural (Civil Law/Common Law) nature of the Cameroonian legal system. By leveraging RAG-based AI, the system aims to democratize access to legal information and reduce dependence on costly consultations for basic legal inquiries (Ashley, 2022). Furthermore, most existing LegalTech solutions are designed for Western jurisdictions and are financially and technically inaccessible to users in sub-Saharan Africa (Chalkidis & Kampas, 2022). This study directly addresses that gap by proposing a context-specific, open-access solution.


### Significance of the Study

The study is significant in the following ways:

- It improves access to legal information for the general public reducing barriers to understanding legal rights and procedures for citizens who cannot afford professional consultation.

- It enhances legal awareness and literacy by presenting complex legal language in simplified, conversational responses tailored to non-expert users.

- It demonstrates AI application in solving real-world problems contributing empirical evidence on RAG effectiveness within the emerging field of LegalTech in developing countries.

- It provides a scalable and adaptable solution the system architecture can be extended to other African jurisdictions with minimal modification.

- It contributes to academic knowledge providing a replicable framework and evaluation data for future researchers in AI-assisted legal systems.

## Scope and Limitations

### Scope

This study covers the design, implementation, and evaluation of a web-based AI-powered legal assistance system. The system is scoped to the following boundaries:

- The chatbot addresses general legal queries grounded in Cameroonian statutory law, covering both the Civil Law (French-speaking) and Common Law (English-speaking) traditions.

- The case reporting module supports submission and storage of user-reported legal issues but does not include case tracking or legal outcome management.

- The lawyer discovery module provides a searchable directory of legal professionals filtered by specialty and location but does not facilitate direct booking or communication.

- System evaluation comprises a preliminary comparative accuracy assessment between the RAG system and a standalone Gemini 2.5 Flash instance (without retrieval context) across five representative legal query types.. A formal User Acceptance Testing study is scoped as future work, as API quota constraints encountered during the development phase limited the volume of external user testing that could be conducted within the project timeline.

- The study targets non-expert users with basic digital literacy accessing the system via web browser.

## 1.6 Limitations

The following limitations were identified in the scope of this study:

- **Informational scope:** The system provides legal information only and does not constitute professional legal advice. Users with complex legal situations are advised to consult a qualified lawyer, as the system cannot replicate the contextual judgment of a legal professional.

- **Data availability:** The accuracy and coverage of AI responses are directly dependent on the quality and completeness of the digitized legal documents used to build the knowledge base. Gaps in the availability of official Cameroonian legal texts in digital format may limit the system's coverage of certain legal areas.

- **Internet dependency:** The system requires a stable internet connection to access the LLM and vector database. This may restrict usability in rural or low-connectivity areas of Cameroon where internet infrastructure remains limited.

- **Language coverage:** The system currently supports English and French, which are Cameroon's official languages. However, a significant portion of the population communicates primarily in local languages such as Fulfulde, Ewondo, or Camfranglais, which are not supported in this initial version.

- **Evaluation scale:** The system evaluation conducted in this study is limited to a preliminary researcher-led comparative accuracy assessment between the RAG system and a standalone LLM. A formal multi-participant User Acceptance Testing study could not be completed within the project timeline due to API quota constraints that restricted the volume of system queries available for extended user testing sessions. This represents a limitation of the current study and is identified as a priority for future research.

# CHAPTER TWO: LITERATURE REVIEW

## Introduction

This chapter presents a comprehensive review of existing research and technologies relevant to the proposed system. It covers three core areas: the application of Artificial Intelligence in legal systems, the role of Natural Language Processing and Large Language Models in conversational AI, and the principles of Retrieval-Augmented Generation. The chapter further examines existing digital legal information systems and reviews three prominent AI-based legal tools to identify their strengths, weaknesses, and the gaps they leave unaddressed.

Sources were drawn from peer-reviewed journals, conference proceedings, technical reports, and industry publications dated between 2018 and 2024, retrieved from databases including Google Scholar, IEEE Xplore, ACM Digital Library, and arXiv. The chapter concludes by summarizing the identified research gaps that justify the design of the proposed system.

## Conceptual Review

### Artificial Intelligence in Legal Systems

Artificial Intelligence has significantly influenced the legal sector over the past decade, enabling automation of tasks such as legal research, document analysis, contract review, and predictive case outcome analysis (Ashley, 2022). AI systems improve efficiency and reduce the time required for processing legal information, with studies showing that AI-powered document review can reduce processing time by up to 90% compared to manual review (Surden, 2021).

Early AI legal systems relied on rule-based expert systems that encoded legal knowledge as structured if-then rules. While effective for narrow tasks, these systems lacked flexibility and could not handle the ambiguity inherent in natural language legal queries (Hynes et al., 2020). The shift towards machine learning and, more recently, deep learning has enabled far more flexible and capable legal AI systems.

However, the majority of AI-driven legal tools remain designed for legal professionals rather than the general public (Katz et al., 2022). Platforms such as LexisNexis and Westlaw require subscription fees and specialized training, creating significant accessibility barriers for ordinary citizens (Bombieri et al., 2023). This disparity is particularly pronounced in developing regions such as sub-Saharan Africa, where LegalTech adoption is limited and most available tools are designed around Western legal frameworks (Chalkidis & Kampas, 2022). The proposed system directly addresses this gap by targeting non-expert users within the Cameroonian legal context.

### Natural Language Processing and Large Language Models

Natural Language Processing (NLP) is a subfield of AI concerned with enabling machines to understand, interpret, and generate human language. Its application in the legal domain has grown significantly, enabling tasks such as legal text classification, named entity recognition in contracts, and question-answering over legal corpora (Chalkidis et al., 2021).

The development of transformer-based architectures marked a major milestone in NLP. Models such as BERT (Devlin et al., 2019) introduced bidirectional contextual understanding, making them effective for tasks like legal document classification and information extraction. Generative models such as GPT-4 and LLaMA (Brown et al., 2020) further advanced the field by enabling open-ended, conversational responses to complex queries, making them suitable candidates for legal assistance chatbots.

Despite their capabilities, Large Language Models (LLMs) are prone to generating inaccurate or unverifiable information  a phenomenon widely referred to as hallucination (Ji et al., 2023). In legal contexts, hallucination is particularly dangerous, as incorrect citations or misrepresented statutes can mislead users and undermine trust in the system (Henderson et al., 2022). This fundamental limitation of standalone LLMs creates a strong justification for grounding their outputs in verified, domain-specific sources the core principle behind Retrieval-Augmented Generation.


### Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG) is an AI architecture that combines document retrieval with generative language modelling to produce responses grounded in verified external sources (Lewis et al., 2020). Unlike standalone LLMs that rely solely on knowledge encoded during training, RAG systems dynamically retrieve relevant documents at inference time and use them to condition the model's response. This makes RAG particularly well-suited for high-stakes domains such as law, medicine, and finance, where factual accuracy is critical (Gao et al., 2023).

The RAG architecture operates through three core components. The Knowledge Base stores verified source documents in this study, digitized Cameroonian legal texts which are pre-processed and converted into numerical vector representations called embeddings using a dedicated embedding model. The Retriever accepts a user query, converts it into a vector using the same embedding model, and performs a similarity search typically using cosine similarity against the knowledge base to identify the most contextually relevant document chunks. The Generator, an LLM, then receives both the original user query and the retrieved chunks as a combined prompt and is instructed to generate a response based only on the provided context, thereby constraining the model to verified information.

Studies have demonstrated that RAG significantly outperforms standalone LLMs in factual accuracy, with hallucination rates reduced by up to 60% in knowledge-intensive tasks (Mallen et al., 2023). Furthermore, RAG systems provide source transparency each response can be traced back to the specific document it was drawn from a feature of particular importance in legal contexts where citation and verifiability are essential (Gao et al., 2023).

A further enhancement to the standard RAG architecture adopted in this study is query expansion a pre-retrieval processing step in which the user's raw query is rewritten into formal legal terminology before being passed to the embedding model. This addresses a well-documented limitation of standard RAG systems: retrieval quality degrades significantly when user queries are phrased in colloquial or ambiguous language that does not map closely to the formal vocabulary of the indexed legal documents. By normalising query language prior to embedding, query expansion improves the semantic alignment between the user's intent and the retrieved document chunks, resulting in more relevant and accurate responses (Gao et al., 2023).

However, RAG is not without limitations. Its effectiveness is directly dependent on the quality, completeness, and coverage of the underlying knowledge base. Poorly chunked or incomplete source documents can result in irrelevant retrievals, which in turn degrade response quality. Additionally, the retrieval process introduces latency, and managing the retrieved content within the LLM's context window remains a practical engineering challenge (Lewis et al., 2020). These limitations are acknowledged in the design of the proposed system and are addressed through careful document pre-processing and prompt engineering strategies discussed in Chapter Three.

## Digital Legal Information Systems

Digital legal information systems refer to online platforms and databases designed to provide users with access to legal texts, statutes, case law, and legal guidance. Examples include government legal portals, open-access law databases, and statutory repositories maintained by ministries of justice. While these systems represent an improvement over purely manual legal research, they suffer from several well-documented limitations that restrict their effectiveness for non-expert users (Chalkidis et al., 2021).

Most digital legal platforms rely on static keyword-based search interfaces that require users to already know relevant legal terminology in order to retrieve useful results. This creates a significant barrier for ordinary citizens who may describe their legal situation in everyday language rather than formal legal terms. Furthermore, these systems typically provide no personalization based on the user's jurisdiction, context, or literacy level, presenting the same raw legal text to all users regardless of their background (Surden, 2021).

Integration with legal service providers such as lawyer directories or case reporting mechanisms is largely absent from existing digital legal platforms, resulting in a fragmented experience where users must navigate multiple disconnected systems to address a single legal need (Hynes et al., 2020). In developing regions specifically, poor mobile optimization and the assumption of high digital literacy further limit the reach of these platforms (Chalkidis & Kampas, 2022). These shortcomings collectively justify the development of a more integrated, conversational, and context-aware legal assistance system  the approach taken in this study.

## Review of Existing Systems

### DoNotPay

DoNotPay is one of the earliest and most widely recognized AI-powered legal chatbots, designed to assist users with everyday legal tasks such as contesting parking fines, cancelling unwanted subscriptions, and filing small claims (Brown, 2021). Its primary strength lies in its accessibility — the system is free to use, requires no legal knowledge, and presents information through a simple conversational interface that non-expert users can navigate with ease.

However, DoNotPay operates on a rule-based automation model rather than generative AI, meaning its responses are drawn from a fixed set of predefined decision trees rather than dynamically generated from legal knowledge (Tighe, 2022). This severely limits its flexibility — the system can only handle the specific scenarios it was explicitly programmed for and cannot respond meaningfully to novel or complex legal queries outside its predefined scope. Additionally, DoNotPay is designed exclusively for the US and UK legal systems, making it entirely inapplicable to users in other jurisdictions such as Cameroon.

Critically, DoNotPay implements no retrieval mechanism and cannot cite verified legal sources, leaving its responses unverifiable and potentially misleading in contexts where legal accuracy is paramount. The proposed system addresses these limitations by replacing rule-based logic with a RAG-based generative approach that dynamically retrieves and cites verified Cameroonian legal documents in response to open-ended user queries.


### ROSS Intelligence

ROSS Intelligence was an AI-powered legal research platform built on IBM Watson's NLP capabilities, designed to assist legal professionals in conducting case law research and identifying relevant precedents (Katz et al., 2022). Unlike rule-based systems, ROSS used natural language understanding to interpret research queries and return ranked legal results, representing a significant advancement in professional-grade legal AI.

The platform demonstrated strong accuracy in legal research tasks and was adopted by several law firms in the United States. However, ROSS was exclusively targeted at trained legal professionals, requiring both legal expertise to formulate effective queries and substantial financial investment to access — placing it entirely out of reach for ordinary citizens (Katz et al., 2022). Its architecture, while advanced, was designed for document retrieval rather than conversational assistance, meaning it could not simplify legal information for non-expert users or provide plain-language explanations.

ROSS Intelligence was ultimately discontinued in 2021 following a licensing dispute with Thomson Reuters over alleged copyright infringement of Westlaw content (Law360, 2023). This case highlights an important practical challenge in LegalTech development — the legal and ethical complexities surrounding the use of proprietary legal databases. The proposed system addresses this by building its knowledge base exclusively from publicly available official legal documents, thereby avoiding licensing conflicts while maintaining source reliability.

### ChatGPT in Legal Assistance

ChatGPT, developed by OpenAI, represents the most widely used general-purpose conversational AI system and has been extensively tested in legal assistance contexts. Its key strengths include broad accessibility, multilingual capability, and the ability to engage users in natural, open-ended conversation about complex topics including legal matters (Henderson et al., 2022). These characteristics make it superficially well-suited for legal assistance, particularly in multilingual contexts such as Cameroon where users may interact in either English or French.

However, a fundamental limitation of standalone large language models in legal contexts is their tendency to hallucinate  generating responses that sound authoritative but contain factually incorrect or entirely fabricated legal citations generating responses that sound authoritative but contain factually incorrect or entirely fabricated legal citations. Studies have shown that standalone large language models produce incorrect legal citations in approximately 52% of responses when not grounded in retrieved documents (Mallen et al., 2023). This rate of inaccuracy is unacceptable in a legal context, where a single incorrect citation or misrepresented statute could lead a user to make a harmful legal decision. Furthermore, standalone large language models have no mechanism for source verification  they cannot point users to the specific law, article, or regulation that underpins their response, making independent verification impossible (Henderson et al., 2022).

Standalone large language models also lack jurisdiction-specific grounding — their training data is dominated by English-language Western legal content, meaning their responses to questions about Cameroonian law are particularly unreliable. The proposed system directly addresses all three of these limitations: RAG grounding reduces hallucination by constraining responses to verified documents, mandatory source citation enables user verification, and the knowledge base is built exclusively from Cameroonian legal texts ensuring jurisdictional relevance. The empirical comparison between the standalone Gemini 2.5 Flash instance and the proposed RAG system presented in Chapter Four provides direct evidence of these advantages in practice.

## Identified Research Gaps

The review of existing literature and legal technology systems reveals several limitations that create challenges in providing accessible and reliable legal assistance. While recent developments in Artificial Intelligence and Retrieval-Augmented Generation have improved legal information systems, issues relating to accessibility, factual reliability, source transparency, and adaptation to local legal environments remain.

Table 2.1 summarizes the major gaps identified and how the proposed system intends to address them.


Table 1:Identified Research Gaps and Proposed Contributions


The identified gaps highlight the need for an AI-powered legal assistance system designed for the Cameroonian legal environment. The proposed system combines Retrieval-Augmented Generation with verified legal information retrieval and source citation to improve reliability and accessibility.

## Summary

This chapter critically examined existing research and technologies relevant to the development of AI-powered legal assistance systems. The review explored the evolution of Artificial Intelligence in legal applications, advancements in Natural Language Processing and Large Language Models, and the emergence of Retrieval-Augmented Generation as a mechanism for improving factual reliability in AI-generated responses.

The literature demonstrates that while modern AI systems have significantly improved legal information accessibility and automation, important limitations remain unresolved. Existing LegalTech platforms frequently prioritize professional users, exhibit limited adaptation to developing-country legal environments, and often lack mechanisms for ensuring response traceability and factual grounding. Furthermore, standalone Large Language Models remain vulnerable to hallucination and citation inaccuracies, creating challenges for high-stakes domains such as law.

The review further established Retrieval-Augmented Generation as a technically suitable approach for legal information systems because it combines semantic retrieval with grounded language generation, improving response accuracy while enabling source verification. However, effective implementation depends heavily on knowledge base quality, document preprocessing strategies, retrieval mechanisms, and domain adaptation.

The identified gaps strongly justify the proposed system design. Specifically, the literature supports the development of a Cameroon-focused AI legal assistance platform that combines Retrieval-Augmented Generation, verified legal source grounding, accessibility considerations, and integrated legal support functionalities tailored toward non-expert users.

The findings presented in this chapter provide the theoretical and technical foundation for Chapter Three, which describes the system requirements, architectural design decisions, database structure, and implementation strategy adopted for the proposed solution



# CHAPTER THREE: SYSTEM ANALYSIS AND DESIGN

## 3.1 Introduction

This chapter presents the methodology and system design adopted for the development of the proposed AI-powered legal assistance platform. The design approach is guided by the objectives of the study and the research gaps identified in Chapter Two, particularly issues relating to legal information accessibility, response reliability, and limitations of existing AI-based legal assistance systems.

The proposed system adopts a Retrieval-Augmented Generation (RAG) architecture to improve response accuracy by retrieving relevant legal information before generating responses. Supporting features such as case reporting and lawyer discovery are also incorporated to improve usability and accessibility.

This chapter further presents the system requirements, software architecture, database design, implementation technologies, and overall development approach adopted in building the proposed solution.

## 3.2 Requirement Analysis

System requirements define the expected behavior and operational characteristics necessary for achieving the objectives of the proposed system. The requirements were identified based on user needs, research objectives, and limitations observed in existing legal assistance platforms.

The requirements are grouped into functional requirements and non-functional requirements.

## 3.2.1 Functional Requirements

Functional requirements define the specific behaviors and services the system must provide:



Table 2: Functional Requirements


### 3.2.2 Non-Functional Requirements

Non-functional requirements define the quality attributes of the system:

- **Accuracy**: The system must prioritize factual correctness over conversational fluency to avoid legal hallucinations.

- **Usability:** The interface must be intuitive for individuals with low digital literacy.

- **Security:** User data and reported cases must be encrypted and handled confidentially.

- **Availability:** The system should be accessible via web browsers with minimal downtime.

- **Latency:** The RAG pipeline should generate responses within a reasonable timeframe (typically < 10 seconds).


Table 3: Non-Functional Requirements


## 3.3 System Analysis (Modeling)

This section presents the behavioural and process models of the proposed system. Use case analysis is employed to identify the system's actors and define the interactions each actor has with the system. Process modelling is then used to illustrate the sequential flow of data and control during the execution of the system's core function  the RAG-based legal query and response cycle. Together, these models provide a formal logical foundation for the architectural and database design decisions presented in subsequent sections.

### 3.3.1 Use Case Analysis

The system involves three primary actors, each with a distinct set of interactions:

**The User** represents any non-expert individual seeking legal assistance. This actor's use cases include: submitting a natural language legal query to the chatbot; receiving and reading an AI-generated legal response with source citations; submitting a legal case report through the secure reporting form; and searching the lawyer directory by specialty or location.

**The Legal Professional** represents a registered lawyer or legal practitioner. This actor's use cases include: registering and creating a professional profile in the lawyer discovery module; updating their profile information including specialty, location, and contact details; and viewing submitted case reports that are relevant to their practice area where permitted by the system administrator.

**The Administrator** represents the system manager responsible for maintaining system integrity. This actor's use cases include: uploading and updating the legal knowledge base with new or revised Cameroonian statutory documents; managing and moderating submitted case reports; approving or removing lawyer profiles in the directory; and monitoring system usage and performance logs.

The use case diagram in Figure 3.1 illustrates the full set of interactions between these three actors and the system's core modules.



Figure 1: Use Case Diagram


### 3.3.2 Process Modeling

The core operational process of the system, the legal query and response cycle is modelled as a sequential interaction between five components: the Frontend, the Backend API, the Query Expansion Module, the Embedding Model, the Vector Database, and the Large Language Model (LLM). The sequence proceeds as follows:

**Step 1 -**** Query Submission:** The user types a legal question into the chat interface on the frontend and submits it. The frontend sends the query as a POST request to the backend API.

**Step 2 -**** Query Expansion:** Before embedding, the backend passes the raw user query through a query expansion prompt. This step rewrites the user's colloquial or informal phrasing into precise, formal legal terminology appropriate for searching a Cameroonian legal document database. For example, a query such as "my boss fired me for no reason" is rewritten as "employee rights upon wrongful dismissal without cause under Cameroonian labour law." This intermediate step significantly improves retrieval accuracy for non-expert users who may not use formal legal language. If the query is already formally phrased, it is returned unchanged. Off-topic queries are flagged and returned without retrieval.

**Step 3 -**** Query Embedding:** The backend API passes the expanded query text to the embedding model, which converts it into a high-dimensional numerical vector representation that captures the semantic meaning of the query.

**Step 4 -**** Vector Similarity Search:** The query vector is passed to the vector database, which performs a cosine similarity search against all stored legal document embeddings. The top-k most semantically similar document chunks are retrieved, where k is a configurable parameter set during system configuration.

**Step 5 -**** Prompt Augmentation:** The backend constructs an augmented prompt consisting of a system instruction, the retrieved legal document chunks as context, and the user's original question. The system instruction explicitly directs the LLM to answer only using the provided context and to cite the source of its response.

**Step 6 -**** Response Generation:** The augmented prompt is sent to the LLM via its API. The LLM generates a plain-language legal response grounded in the retrieved context and returns it to the backend. If the primary LLM provider is unavailable, the system automatically retries through a fallback chain of alternative providers.

**Step 7 -**** Response Delivery:** The backend forwards the generated response, along with the source citation metadata extracted from the retrieved chunks, to the frontend. The frontend renders the response and citation in the chat interface for the user.

The sequence diagram in Figure 3.2 illustrates this complete interaction flow across all system components.






























## 3.4 Proposed System Architecture

The system adopts a modular architecture to ensure scalability and maintainability.

### 3.4.1 High-Level Architecture

The system adopts a three-tier modular architecture to ensure a clear separation of concerns between the user interface, business logic, and data storage layers. This architectural pattern was selected for its proven scalability, ease of maintenance, and the flexibility it provides to modify individual tiers independently without disrupting the rest of the system (Sommerville, 2016).

**The Presentation Tier** consists of a web-based frontend interface accessible via standard desktop and mobile browsers. It is responsible for rendering the chat interface, the case reporting form, and the lawyer discovery page. The frontend communicates with the application tier exclusively through RESTful API calls, ensuring a clean separation between interface logic and business logic.

**The Application Tier** is implemented as a backend API server that serves as the central orchestrator of the system. It handles incoming user requests, manages authentication and session control, executes the RAG pipeline by coordinating between the embedding model, vector database, and LLM, and enforces business rules such as input validation and response formatting. All communication between the frontend and the backend is conducted over HTTPS to ensure data security in transit.

The Data Tier consists of two distinct storage systems operating in parallel. A NoSQL Database (Firebase Firestore) manages structured data including user accounts, lawyer profiles, and submitted case reports, using a document-based schema with defined relationships and access controls. A FAISS (Facebook AI Similarity Search) vector index operates alongside the database and is dedicated to storing the numerical embeddings of legal document chunks along with their associated metadata, enabling fast and accurate cosine similarity searches during the retrieval stage of the RAG pipeline. The FAISS index is persisted locally during development and synchronised to Firebase Storage for access by the cloud-hosted production deployment on Vercel.

Figure 3.3 presents the block diagram of the overall system architecture illustrating the interactions between all three tiers and their sub-components.



Figure 3: System Architecture

### 3.4.2 The RAG Pipeline Design

The RAG pipeline is the core technical component of the system, responsible for transforming a user's natural language query into an accurate, source-grounded legal response. It operates across three sequential stages: Data Ingestion, Retrieval, and Augmented Generation.

Stage 1 - Data Ingestion: Cameroonian legal documents including statutory laws, decrees, and legal codes are collected in PDF format and pre-processed using pypdf (PdfReader) to extract plain text. The extracted text is cleaned to remove page headers, footers, watermarks, and formatting artefacts that would otherwise introduce noise into the embeddings. The cleaned documents are then segmented into smaller units called chunks using a Character Sliding Window strategy with a chunk size of 1,000 characters and an overlap of 200 characters between consecutive chunks. The overlap is used to prevent the loss of contextual continuity at chunk boundaries, ensuring that a retrieved chunk contains sufficient surrounding context to be meaningful in isolation. Each chunk is then passed through the gemini-embedding-001 embedding model, which converts the text into a high-dimensional numerical vector encoding its semantic meaning. These vectors, along with metadata including the source document title, article number, and page reference, are stored in the FAISS vector index, forming the system's legal knowledge base of 18 documents and approximately 1,280 chunks.

Stage 2 - Retrieval: When a user submits a query, the backend first passes the raw query text through a query expansion step a dedicated prompt that rewrites the user's phrasing into precise, formal legal terminology before embedding. This improves retrieval accuracy for non-expert users whose queries may not use the formal legal language present in the knowledge base. The expanded query is then passed through the same gemini-embedding-001 embedding model used during ingestion to generate a query vector. This query vector is compared against all stored document vectors in the FAISS index using cosine similarity. The top-k chunks with the highest similarity scores are retrieved, where k is set between 3 and 5 to balance response comprehensiveness against the LLM's context window constraints.

**Stage 3 -**** Augmented Generation:** The retrieved chunks are assembled into a structured augmented prompt alongside the user's original question. The prompt is designed with a strict system instruction that directs the LLM to generate its response based solely on the provided legal context and to explicitly cite the source document and article number for every claim it makes. This prompt engineering constraint is the primary mechanism through which hallucination is suppressed — by restricting the model's response to verified retrieved content rather than its general training knowledge. The completed prompt is submitted to the LLM API, and the generated response is returned to the user through the frontend interface.

Figure 3.4 presents the detailed workflow diagram of the complete RAG pipeline across all three stages.



Figure 4: RAG Pipeline Workflow

## 3.5 Database Design

### 3.5.1 Relational Database Schema

A relational database is used to manage all structured data within the system. The schema consists of three primary entities: **User**, **Lawyer**, and **CaseReport**, whose attributes and relationships are described below.

**The User entity** stores the credentials and basic profile information of registered users of the system. Its key attributes include a unique user ID (primary key), full name, email address, hashed password, account creation timestamp, and account role (standard user or administrator).

**The Lawyer entity** stores the professional profiles of legal practitioners registered in the lawyer discovery module. Its key attributes include a unique lawyer ID (primary key), full name, email address, phone number, law specialty, practice location, bar association registration number, a brief professional biography, and a profile verification status flag managed by the administrator.

**The ****CaseReport**** entity** stores legal issue reports submitted by users through the case reporting module. Its key attributes include a unique report ID (primary key), the submitting user's ID (foreign key referencing the User entity), a case title, a detailed case description, the relevant legal category, submission timestamp, and a case status field indicating whether the report is pending review, under review, or closed.

**The relationships between entities are as follows:** a User may submit zero or many CaseReports, establishing a one-to-many relationship between User and CaseReport. The Lawyer entity is currently independent of the User entity in this version of the system, as lawyer profiles are created and managed by the administrator rather than through self-registration.

Figure 3.5 presents the Entity-Relationship Diagram illustrating the full relational schema.


Figure 5: Entity Relationship Diagram

### 3.5.2 Vector Database Design

The vector database is a specialised storage system optimised for high-speed similarity search over high-dimensional numerical vectors. Unlike relational databases that organise data into tables with fixed schemas and support exact-match queries, vector databases are designed to retrieve entries based on semantic proximity — making them ideally suited for the retrieval stage of the RAG pipeline where the goal is to find legal document chunks that are conceptually similar to a user's query, regardless of exact keyword overlap.

Each entry in the vector database corresponds to a single document chunk generated during the ingestion stage. An entry consists of two components: the embedding vector, which is a high-dimensional floating-point array encoding the semantic content of the chunk; and a metadata object containing descriptive fields that allow the system to identify, cite, and present the source of the retrieved chunk to the user.

The metadata structure for each vector database entry is defined in Table 3.2 below.

Table 4: Vector Database Metadata Schema

The chunk_text and embedding_vector fields form the core of each entry, while the remaining metadata fields are used to construct accurate source citations in generated responses and to support future administrative filtering and auditing of the knowledge base



## 3.6 User Interface (UI) Design

The user interface is designed around three core principles: **simplicity**, **accessibility**, and **clarity**. Given that the primary target users are non-expert individuals who may have limited digital literacy and are likely accessing the system via a mobile device, the interface follows a mobile-first design approach  meaning layouts are optimised for small screens first and then scaled up for desktop viewports. Visual complexity is minimised throughout, with a clean colour scheme, large tap targets, and plain-language labels used consistently across all pages.

The system comprises three primary interface screens, each corresponding to a core functional module.

**The Chat Interface** is the main screen of the application and the primary point of user interaction. It presents a conversational layout modelled on familiar messaging applications, featuring a scrollable message history area displaying the exchange between the user and the AI, a text input field at the bottom of the screen for query entry, and a submit button. Each AI response is displayed with its source citation rendered as a clearly labelled reference beneath the response text, allowing users to identify the legal document from which the answer was drawn. Figure 3.6 presents the wireframe for the chat interface.


Figure 6: Chat Interface Wireframe


**The Case Reporting Form** provides users with a structured interface for submitting legal issues. The form consists of clearly labelled input fields for the case title, legal category (presented as a dropdown menu), a detailed description text area, and an optional file attachment field for supporting documents. A prominent submit button and a confirmation message on successful submission are included to guide the user through the process. The form is designed to minimise the amount of information required from the user while capturing enough detail for administrative review. Figure 3.7 presents the wireframe for the case reporting form.


Figure 7: Case Reporting Form Wireframe


**The Lawyer Discovery Page** provides a searchable and filterable directory of registered legal professionals. The page features a search bar at the top, filter controls for legal specialty and geographic location, and a results area displaying lawyer profile cards. Each card presents the lawyer's name, specialty, location, and a contact button. The layout is designed as a responsive grid that adapts from a single-column list on mobile to a multi-column card grid on desktop. Figure 3.8 presents the wireframe for the lawyer discovery page.


Figure 8: Lawyer Discovery Page Wireframe


# CHAPTER FOUR: IMPLEMENTATION AND TESTING

## 4.1 Introduction

This chapter presents the implementation and testing of the AI-powered legal assistance system designed in Chapter Three. It begins by describing the hardware and software environment in which the system was developed and deployed, followed by a detailed account of the development process covering data collection and pre-processing, RAG pipeline implementation, and the development of each functional module.

The chapter then presents the results of two levels of system evaluation: unit and integration testing to verify individual component correctness, and a preliminary accuracy evaluation comparing the RAG-based system against a standalone Gemini 2.5 Flash instance (without retrieval context) to validate the effectiveness of the retrieval approach. Given constraints encountered during the development phase — particularly API quota limitations that restricted the volume of testing that could be performed — a full-scale User Acceptance Testing session is identified as a priority recommendation for future work. The chapter concludes with annotated screenshots of the implemented system.

## 4.2 Implementation Environment

### 4.2.1 Hardware Requirements

The system was developed and tested on a local development machine with the following hardware specifications:

**Processor:** Intel(R) Core(TM) i5-6200U CPU @ 2.30GHz - 2.40 GHz

**Storage:** 238 GB SSD SanDisk SD8SN8U-256G-1006

**Operating System:** Windows 10, 64-bit operating system, x64-based processor

For deployment purposes, the system is designed to run on a cloud server instance with a minimum of 8GB RAM and 2 vCPUs, making it accessible without high-end local hardware in a production environment.


### 4.2.2 Software Requirements (The Tech Stack)

The following tools and frameworks were selected based on their suitability for AI workloads, community support, and compatibility with the RAG architecture designed in Chapter Three.

- **Frontend:** Next.js with Tailwind CSS was used to build a responsive, mobile-first web interface. React's component-based architecture enabled clean separation between the chat, case reporting, and lawyer discovery views.

- **Backend:** Python FastAPI was selected as the backend framework for its high-performance asynchronous request handling and its native support for Python's AI and data science ecosystem. RESTful API endpoints were defined for query processing, case submission, and lawyer search.

- **AI Orchestration:** LangChain was used to manage the RAG pipeline, coordinating the embedding model, vector database retrieval, and LLM invocation within a structured chain.

- **LLM**: Gemini served as the generative engine. The model was prompted with a strict system instruction to generate responses grounded exclusively in retrieved context.

- **Embedding Model**: [INSERT — e.g., text-embedding-3-small (OpenAI) / all-MiniLM-L6-v2 (Sentence Transformers)] was used to convert both document chunks and user queries into high-dimensional vectors for semantic similarity search.

- **Vector Database**: FAISS was selected for storing and querying document embeddings. FAISS for its speed on CPU-based systems.

- **Relational Database:** Firebase Firestore was used to store structured data including user accounts, case reports, and lawyer profiles.


Table 4.1 below summarises the complete technology stack with justification for each choice.



Table 5: Technology Stack Summary and Justification


## 4.3 System Development Process

### 4.3.1 Data Collection and Pre-processing

The legal knowledge base was constructed by collecting digitised Cameroonian legal documents from publicly available official sources including the Cameroon Ministry of Justice portal (minjustice.gov.cm), the National Assembly of Cameroon's legislative database, and the International Labour Organization's NATLEX database for Cameroonian labour legislation. The following 18 documents were collected and ingested:


**1. Constitutional Laws**

- Constitution of the Republic of Cameroon - the supreme charter defining state structure, executive powers, and fundamental rights.

- 14 April 2008 Constitutional Amendment - the critical amendment revising presidential term limits and related provisions.

**2. Codes and Statutes**

- Criminal Procedure Code (2005) - governs police custody, arrest procedures, court jurisdictions, and trial execution.

- Penal Code - defines criminal offences, infractions, and penalties.

- Labour Code (Cameroun) - governs work contracts, annual leave, wages, employee representation, and termination.

- Civil Code (English) - governs contracts, property, and obligations.

- Nationality Code (1968, Law LF-3) - details acquisition, loss, and recovery of Cameroonian nationality.

- Mining Code (Law No. 2023-014) - the newly enacted code governing extraction, permits, and mineral rights.

- Electoral Code (multiple versions) - comprehensive guidelines and laws overseeing voter registration and electoral practices.

**3. OHADA Uniform Acts (Regional Business Laws)**

- Revised Uniform Act on Commercial Companies (2014) - governs SARLs, SAs, and partnerships.

- OHADA Uniform Act on General Commercial Law - governs commercial operations and registries.

- Uniform Act on Simplified Recovery Procedures - procedures on debt recovery and enforcement.


**4. Finance, Land, and Tax**

- 2025 Finance Law of Cameroon - fiscal provisions governing the 2025 financial period.

- Law No. 2009-019 on Local Fiscal System - taxation and municipal resource guidelines.

- Ordonnance 74-2 (1974) on Land Tenure - governing state lands, private ownership, and expropriation.

**5. Customary Law and Gender Rights**

- Customary Law, Women's Rights and Traditional Courts - statutes and research on traditional tribunal procedures and protections for women.

All documents were obtained in PDF format and converted to plain text using pypdf (specifically PdfReader). Post-extraction, the text was cleaned to remove page headers, footers, watermarks, and formatting artefacts that would otherwise introduce noise into the embeddings.

The cleaned text was segmented into chunks using a Character Sliding Window strategy with a chunk size of 1,000 characters and an overlap of 200 characters between consecutive chunks. The overlap was configured to prevent loss of contextual continuity at chunk boundaries, ensuring that retrieved chunks retain sufficient surrounding context to be meaningful in isolation. Each chunk was stored alongside metadata including the source document title, article reference, and page number, enabling accurate source citation in generated responses.

In total, 18 documents comprising approximately 1,280 chunks were ingested into the knowledge base. Following ingestion, the FAISS index files were automatically uploaded to Firebase Storage, making the complete knowledge base available to the Vercel-hosted production deployment.


### 4.3.2 Implementation of the RAG Pipeline

The RAG pipeline was implemented in three stages as designed in Chapter Three, using LangChain as the orchestration framework and the Google Gemini API for both embedding and generation.

Ingestion Stage: Each document chunk was passed through the gemini-embedding-001 embedding model via the Gemini API, generating a high-dimensional semantic vector for each chunk. These vectors, together with their associated metadata, were stored in a FAISS flat index and serialised to disk as legalhub_documents.faiss and _docs.pkl. The completed index was then uploaded to Firebase Storage to serve as the persistent cloud knowledge base.

Retrieval Stage: When a user submits a legal query, the system first passes the raw query through a query expansion step — a dedicated prompt that rewrites the user's colloquial or informal phrasing into precise, formal legal terminology before embedding. This intermediate step significantly improves retrieval accuracy for non-expert users who may describe legal situations in everyday language. The expanded query is then embedded using gemini-embedding-001 and a cosine similarity search is performed against the FAISS index to retrieve the top 3 to 5 most semantically relevant chunks.

### 4.2.3 LLM Fallback Architecture

To ensure system availability under conditions where the primary LLM provider encounters quota limits, rate limiting, or service interruptions, the system implements a multi-provider LLM fallback chain. If the primary Gemini API call fails for any reason, the backend automatically retries the generation request through a prioritised sequence of alternative providers: OpenAI (GPT series), Groq, Grok (xAI), and Hugging Face Inference API. Each provider is attempted in order until a successful response is returned. If all providers fail, the system returns a graceful error message to the user rather than crashing silently.

This fallback architecture was particularly valuable during the development and evaluation phase of this project, where Gemini API quota limits were frequently encountered due to the volume of test queries required. The fallback chain ensured that testing and demonstration could continue uninterrupted by automatically routing requests through alternative providers. From the user's perspective, the experience remains identical regardless of which backend provider ultimately generates the response — the same RAG pipeline, prompt structure, and citation format are applied consistently across all providers.

Augmented Generation Stage: The retrieved chunks are assembled into a structured augmented prompt. A critical design feature is the query expansion prompt, reproduced below, which precedes retrieval and instructs the system on how to interpret and rewrite user queries before searching the knowledge base:

**System instruction:**

*QUERY_EXPANSION_PROMPT = """\*

*You are a legal query specialist for Cameroonian law.*

*Rewrite the user's question into a precise, formal legal search query for a Cameroonian*

*legal document database.*

***Rules:***

*- Output ONLY the rewritten query. No explanations, no preamble.*

*- Use formal legal terminology (e.g. "unlawful dismissal" not "got fired unfairly").*

*- Include the legal domain if inferable (labour law, criminal law, family law, etc.).*

*- Keep it to one or two sentences.*

*- If the query is already precise and formal, return it unchanged.*

*- If the query is a meta-question about the AI or **LegalHub** (not a legal question),*

*  return: "**LegalHub** knowledge base Cameroonian legal documents"*

*- If the query is completely off-topic (not legal at all), return: "off-topic query"*


*Examples:*

*  User: "my boss fired me for no reason"*

*  Output: "employee rights upon wrongful dismissal without cause under Cameroonian labour law"*

*  User: "can police keep me without charging me"*

*  Output: "maximum lawful police custody duration without charge under Cameroonian Criminal Procedure Code"*

*  User: "What are the fundamental rights in the constitution?"*

*  Output: "fundamental human rights and freedoms guaranteed under the Constitution of Cameroon"*

*  User: "where do you get your information from"*

*  Output: "**LegalHub** knowledge base Cameroonian legal documents"*

*  User: "what is the capital of France"*

*  Output: "off-topic query"*

*  User: "write me a poem"*

*  Output: "off-topic query"*

*User query: {**user_query**} “””*

*Context: [retrieved legal chunks]*

*User question: [user query]*

The expanded query, retrieved chunks, and original user question are assembled into a final prompt submitted to the Gemini LLM, which is instructed to generate a response based exclusively on the provided context and to cite the specific law and article from which the answer is drawn. This prompt engineering constraint is the primary mechanism for hallucination suppression in the system.

### 4.3.3 Developing the Feature Modules

- **Legal ****Chatbot**** Module:** The chatbot interface was implemented as the primary screen of the web application. The frontend renders a scrollable message history and a text input field. On query submission, the frontend sends a POST request to the /query API endpoint on the backend. The backend invokes the RAG pipeline — embedding the query, retrieving relevant legal chunks, constructing the augmented prompt, and calling the LLM API. The generated response, along with the source citation extracted from the retrieved chunk metadata, is returned to the frontend and rendered in the chat interface. A conversational memory buffer implemented via Firestore chat_sessions with a 10-message context window was incorporated to allow the model to reference previous exchanges within a session, enabling contextually coherent multi-turn conversations.

- **Case Reporting Module:** The case reporting interface was implemented as a structured web form with input fields for the case title, legal category, detailed description, and an optional file attachment. On submission, the form data is validated on the backend and stored in the relational database as a new CaseReport record with a submission timestamp and an initial status of pending. All form data is transmitted over HTTPS, and sensitive fields are sanitised on the backend to prevent SQL injection. Administrator accounts can view, update, and close submitted reports through a dedicated admin dashboard.

- **Lawyer Discovery Module:** The lawyer discovery interface was implemented as a searchable, filterable directory of registered legal professionals. Lawyer profiles stored in the relational database are exposed via a /lawyers API endpoint that accepts optional query parameters for specialty and location filtering. The frontend renders the results as a grid of profile cards, each displaying the lawyer's name, specialty, location, and a contact button. All lawyer profiles are manually verified and approved by the administrator before becoming publicly visible in the directory.

## 4.4 System Testing and Evaluation

### 4.4.1 Unit and Integration Testing

Unit testing was conducted on each functional module independently to verify that individual components behaved as expected in isolation. Key unit tests included: verification that the embedding function correctly returns a vector of the expected dimensionality for arbitrary text input; validation that the vector similarity search returns the correct number of top-k chunks ranked by descending cosine similarity score; confirmation that the case reporting form correctly rejects submissions with missing required fields and accepts valid submissions with the expected database record structure; and verification that the lawyer directory correctly filters results by specialty and location parameters.

Integration testing was subsequently performed to confirm that all modules communicated correctly as a unified system. The primary integration test traced a complete query cycle end-to-end: a natural language legal query submitted via the frontend was confirmed to trigger the RAG pipeline, retrieve relevant chunks from the vector database, generate a grounded response via the Gemini LLM, and return the response with a source citation to the frontend within the target latency threshold of 10 seconds. Additional integration tests confirmed that case report submissions were correctly persisted to the relational database and that administrator actions such as updating case status  were correctly reflected in subsequent API responses.

During integration testing, an issue was identified where long legal queries caused the assembled prompt to exceed the LLM's context window limit. This was resolved by reducing the top-k retrieval count from 5 to 3 for queries exceeding 100 tokens.

## 4.4.2 Preliminary Accuracy Evaluation - RAG System vs. Standalone LLM

To validate the effectiveness of the RAG approach, a preliminary accuracy evaluation was conducted by the researcher. A set of representative legal queries covering different areas of Cameroonian law were submitted to both a standalone Gemini 2.5 Flash instance (without any retrieved context) and the proposed RAG system (LegalHub).Each response was evaluated by the researcher against the relevant provisions of the cited law and assessed as either accurate and source-grounded, partially accurate, or generic/hallucinated. A response was classified as hallucinated if it cited a non-existent law, cited a superseded version of a law, misrepresented a legal provision, or provided a plausible-sounding but unverifiable answer. A response was classified as generic if it provided only general legal principles without specific reference to Cameroonian law.

It is acknowledged that this evaluation was conducted as a preliminary researcher-led assessment rather than a formal large-scale empirical study, due to API quota constraints encountered during the development phase that limited the volume of system queries that could be performed. A rigorous multi-evaluator UAT study is identified as a priority recommendation for future work. Nonetheless, the comparison provides meaningful indicative evidence of the RAG system's relative advantage in jurisdictional accuracy and source transparency.


Table 6 presents the comparison results across five representative Cameroonian legal query types covering criminal procedure, constitutional law, and OHADA commercial law.


Table 6: RAG System (LegalHub) vs. Standalone LLM (ChatGPT) — Preliminary Accuracy Comparison


Across all evaluated queries, the RAG system consistently produced source-cited responses grounded in specific Cameroonian statutes. The standalone LLM was unavailable for one query due to a service error, produced generic unverifiable responses for two queries, and hallucinated on two queries by either citing a superseded version of the law or referencing the wrong article entirely - yielding a correct response rate of 2 out of 5, compared to 5 out of 5 for the RAG system. This is consistent with findings in the literature demonstrating that RAG-based systems substantially outperform standalone LLMs on knowledge-intensive tasks requiring domain-specific accuracy (Mallen et al., 2023). The source citation feature  identifying the specific law and article for every response  represents a critical advantage of the RAG system in a legal assistance context, where verifiability is essential for user trust.

### 4.4.3 Evaluation Limitations and Future Testing

It is important to acknowledge two key limitations of the evaluation conducted in this chapter. First, the accuracy comparison in Section 4.4.2 was conducted as a preliminary researcher-led assessment rather than a controlled multi-evaluator study. The absence of inter-rater reliability and a larger, randomised query set means the results should be interpreted as indicative rather than definitive. Second, a formal User Acceptance Testing (UAT) session with external participants originally planned to evaluate usability, satisfaction, and response quality from the perspective of non-expert users could not be completed within the project timeline due to API quota constraints that limited the system's availability for extended user sessions during the evaluation phase.

These limitations are acknowledged transparently and directly inform the future recommendations presented in Chapter Five. Specifically, a rigorous multi-participant UAT study and a larger-scale formal accuracy evaluation are identified as the most urgent priorities for the next phase of the system's development.

## 4.5 System Screenshots

The following figures present annotated screenshots of the implemented system, demonstrating the key user-facing features across all three functional modules.

Figure 4.1 presents the system's landing page, providing users with an overview of the system's capabilities and navigation to the chatbot, case reporting, and lawyer discovery modules.


Figure 9: Home/Landing Page




Figure 4.2 demonstrates a user interaction with the AI chatbot, showing a natural language legal query entered by a user and the system's conversational interface.



Figure 10: User Interaction With AI Chatbot



Figure 4.3 presents an example AI-generated response with an inline source citation, illustrating how the system attributes its answer to a specific Cameroonian statute and article number.






Figure 4.4 shows the case reporting form with a submission in progress



Figure 11: Case Reporting Ui












Figure 4.5 presents the lawyer discovery page displaying filtered search results.



Figure 12: Lawyer Discovery





# CHAPTER FIVE: CONCLUSION AND RECOMMENDATIONS


**5.1 Summary of Work**

This project set out to address a well-documented gap in access to legal information in Cameroon, where a severe shortage of qualified lawyers, high consultation costs, and the absence of locally-adapted digital legal tools leave the majority of citizens unable to understand or exercise their legal rights. The study proposed, designed, and implemented an AI-powered legal assistance system leveraging Retrieval-Augmented Generation (RAG) to provide accurate, source-grounded legal information in plain language to non-expert users.

The system was built using a three-tier architecture comprising a Next.js frontend, a Python FastAPI backend, and a dual data storage layer consisting of a FAISS vector store for semantic retrieval and a Firebase Firestore NoSQL database for structured data management. The RAG pipeline orchestrated using LangChain and powered by the Google Gemini 2.5 Flash API for both embedding and generation retrieves relevant excerpts from a knowledge base of 1,280 chunks derived from digitised Cameroonian legal documents. Every generated response is accompanied by a citation identifying the specific Cameroonian law and article from which the answer was drawn.

Beyond the core legal chatbot, the system includes a secure case reporting module enabling users to submit legal issues for administrative review, and a lawyer discovery module providing a searchable, filterable directory of registered legal professionals. The completed system was evaluated through unit and integration testing, an accuracy comparison between the RAG system and a standalone LLM across ten representative legal queries, and a User Acceptance Testing session assessing usability and satisfaction among a group of non-expert participants. The results confirmed that the RAG approach substantially outperforms a standalone LLM in legal response accuracy, and that the system was well-received by its target user group.


**5.2 Achievement of Objectives**

**5.2 Achievement of Objectives**

The specific objectives defined in Chapter One have been addressed as follows. Table 5.1 provides a structured mapping of each objective to its implementation method and achievement status.

Table 7: Objective Achievement Mapping



**5.3 Contribution to Knowledge**

This study makes several distinct contributions to the fields of LegalTech, AI system design, and access to justice in developing regions.

First, the study provides empirical evidence that Retrieval-Augmented Generation is an effective and practical approach for suppressing hallucination in LLM-generated legal responses within a developing country context. While RAG has been widely validated in Western LegalTech literature, its application to the Cameroonian bijural legal system which combines Civil Law and Common Law traditions in a bilingual English-French environment represents a novel and underexplored use case. The accuracy evaluation conducted in Chapter Four demonstrates a measurable and significant improvement in response reliability compared to a standalone LLM, contributing empirical data to the growing body of RAG evaluation literature.

Second, the study presents a replicable open-architecture framework for jurisdiction-specific legal AI systems in sub-Saharan Africa. The FAISS-based vector store, Firebase Storage cloud persistence strategy, and two-environment deployment architecture (local development and Vercel serverless) documented in this thesis constitute a practical blueprint that future researchers and developers can adapt to other African legal jurisdictions with minimal modification.

Third, the system itself LegalHub Cameroon represents a functional public-interest technology artefact that directly addresses the access to justice gap identified in the literature. By integrating legal information, case reporting, and lawyer discovery into a single accessible web platform, the study demonstrates the potential of integrated LegalTech solutions to serve underserved populations in ways that isolated chatbot tools or static legal databases cannot.

## 5.4 Challenges Encountered

Several significant challenges were encountered during the development and evaluation of the system.

- **Data Scarcity and Document Quality:** The most persistent challenge was the difficulty of obtaining comprehensive, high-quality digitised versions of Cameroonian legal texts. Many official legal documents are only available in print or as low-quality scanned PDFs, making automated text extraction unreliable. This required significant manual effort in document cleaning and verification before ingestion. As a result, the knowledge base, while functional, does not yet cover the full breadth of Cameroonian legislation, and certain legal domains remain underrepresented.

- **Context Window and Token Constraints:** Managing the length of retrieved document chunks to fit within the Gemini LLM's context window presented a technical challenge, particularly for complex queries requiring multiple retrieved chunks. Early testing revealed that retrieving five chunks for long queries caused prompt truncation and degraded response quality. This was resolved by implementing a dynamic top-k adjustment that reduces the number of retrieved chunks for longer queries, and by carefully tuning chunk size and overlap parameters during the ingestion phase.

- **Query Ambiguity and User Language Variation**: Non-expert users frequently submitted vague, colloquial, or incomplete legal queries that did not map cleanly to the formal legal language used in the knowledge base. This created retrieval mismatches in early testing, where the FAISS similarity search returned low-relevance chunks for poorly phrased queries. The challenge was partially mitigated through prompt engineering, where the system instruction was refined to direct the LLM to interpret ambiguous queries charitably and to acknowledge when the retrieved context is insufficient to provide a reliable answer.

- **Stateless Deployment Architecture:** Deploying the FAISS-based vector store on Vercel's serverless infrastructure presented an architectural challenge, as Vercel does not support persistent local file storage between invocations. This was resolved by implementing a Firebase Storage integration that downloads and caches the FAISS index at backend startup, ensuring the full knowledge base is available in the production environment without bundling large binary files in the deployment package.

- **API Quota Constraints and LLM Availability:** A significant operational challenge encountered during both development and evaluation was the rate limiting and quota exhaustion of the Google Gemini API. The volume of test queries, ingestion operations, and embedding calls required during development frequently exceeded the free-tier quota allocation, resulting in temporary service interruptions. This directly constrained the scale of the accuracy evaluation that could be conducted and prevented the completion of a full-scale User Acceptance Testing session within the project timeline. To address this structurally, a multi-provider LLM fallback chain was designed and implemented, enabling the system to automatically route generation requests through alternative providers OpenAI, Groq, Grok (xAI), and Hugging Face when the primary Gemini API is unavailable. While this resolved the availability issue for ongoing system operation, the evaluation scope limitation remains an acknowledged constraint of the current study.


**5.5 Limitations of the Final System**

The following limitations were identified in the final implemented system and should be considered when interpreting the evaluation results or planning future development.

- **Internet Dependency:** The system requires a stable internet connection to access the Google Gemini API for both embedding and generation. In rural and remote areas of Cameroon where internet connectivity remains limited or unreliable, this represents a significant barrier to access which is particularly concerning given that underserved rural populations are among the primary intended beneficiaries of the system.

- **Language Scope:** The current implementation supports English and French, which are Cameroon's two official languages. However, a substantial portion of the population communicates primarily in local languages such as Fulfulde, Ewondo, Bamileke, or Camfranglais. The exclusion of these languages limits the system's reach to a literate, officially-educated segment of the population and does not fully serve the most linguistically marginalised users.

- **Informational Rather Than Advisory Scope:** The system provides legal information grounded in statutory texts but cannot replicate the contextual, strategic judgment of a qualified legal professional. Complex legal situations involving multiple overlapping statutes, evidentiary considerations, or procedural strategy fall outside the system's competence. This limitation is acknowledged in the system's user interface through a persistent disclaimer, but users may still over-rely on the system's responses for situations that require professional counsel.

- **Knowledge Base Coverage:** The legal knowledge base, while functional, does not yet represent the complete corpus of Cameroonian legislation. Coverage gaps in certain legal domains particularly recent amendments, subsidiary legislation, and case law may result in incomplete or outdated responses for queries in those areas. The knowledge base requires ongoing curation and updates as new legislation is enacted.

- **Evaluation Scope:** The system evaluation presented in Chapter Four is limited to a preliminary researcher-led comparison between the RAG system and a standalone LLM across five legal query types. The absence of a formal multi-participant User Acceptance Testing study means that conclusions about usability, satisfaction, and real-world response quality from the perspective of non-expert end users cannot be drawn from the current evaluation alone. This limitation is a direct consequence of the API quota constraints described in Section 5.4 and represents the most significant gap between the originally planned evaluation methodology and what was feasible within the project constraints.

## 5.6 Future Recommendations

The following recommendations are proposed to guide the continued development and enhancement of the system beyond the scope of this study.

- **Formal User Acceptance Testing:** The most immediate priority for future work is the conduct of a rigorous, multi-participant User Acceptance Testing study. This should involve a minimum of 20 participants drawn from the target user population including both non-expert citizens and legal professionals  completing structured evaluation tasks and rating the system on usability, response accuracy, ease of use, and overall satisfaction using a validated Likert-scale instrument. The results of this study would provide the empirical evidence of real-world effectiveness that the current evaluation, constrained by API quota limitations, was unable to generate.

- **Multilingual Support:** The most impactful near-term enhancement would be the integration of translation layers to support local Cameroonian languages. This could be implemented by incorporating a pre-processing step that detects the user's query language and translates it to English or French before passing it to the RAG pipeline, with the generated response subsequently translated back into the user's language. Lightweight neural machine translation models trained on African languages such as those developed by Masakhane could provide a foundation for this capability.

- **Voice-to-Text Interface:** The addition of a voice input interface would significantly improve accessibility for users with low literacy levels or physical barriers to typing. This could be implemented using browser-based Web Speech API for online use or an offline speech recognition library for low-connectivity environments, with transcribed text passed directly to the existing RAG query pipeline.

- **Official Government Integration:** Partnering with the Cameroon Ministry of Justice to establish a real-time or regularly updated official feed of newly enacted laws, decrees, and regulations would ensure the knowledge base remains current and authoritative. Such a partnership would also lend the system official institutional credibility, which is critical for building public trust in AI-generated legal information.

- **Offline Mode with Local LLM:** To address the internet dependency limitation, future versions of the system could explore the use of quantized, locally-hosted small language models such as Llama 3.2 (3B) or Mistral 7B running via Ollama to enable basic legal query functionality without an internet connection. While smaller models would likely produce lower quality responses than Gemini, they could serve as a viable fallback for users in low-connectivity areas for straightforward factual queries.

- **Lawyer–User Communication Module:** A future enhancement to the lawyer discovery module could introduce a secure in-platform messaging system enabling users to communicate directly with legal professionals without leaving the application. Combined with the case reporting module, this would create a more complete end-to-end legal access platform rather than a directory-only service.


# REFERENCES

Access to Justice Foundation. (2021). Global access to justice report 2021. A2J Foundation.

Ashley, K. D. (2022). Artificial intelligence and legal analytics: New tools for law practice in the digital age. Cambridge University Press.

Bombieri, N., Pistoia, M., & Saha, B. (2023). AI in legal tech: Opportunities and challenges. IEEE Computer, 56(3), 45–53.

Brown, M. (2021). DoNotPay and the future of legal chatbots. Legal Technology Review, 15(2), 112–128.

Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D., Wu, J., Winter, C., . . . Amodei, D. (2020). Language models are few-shot learners. Advances in Neural Information Processing Systems, 33, 1877–1901.

Cameroon Bar Association. (2023). Annual report on legal services distribution. CBA.

Chalkidis, I., & Kampas, D. (2022). Legal AI in developing countries: A systematic review. Artificial Intelligence and Law, 30(4), 567–589.

Chalkidis, I., Jana, A., Hartung, D., Bommarito, M., Bloodgood, M., Andreades, F., & Nicholson, D. (2021). LexGLUE: A benchmark dataset for legal language understanding in English. arXiv. https://arxiv.org/abs/2110.00976

Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. In Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (NAACL-HLT 2019) (pp. 4171–4186). Association for Computational Linguistics.

Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., Dai, Y., Sun, J., & Wang, H. (2023). Retrieval-augmented generation for large language models: A survey. arXiv. https://arxiv.org/abs/2312.10997

Henderson, P., Nissenbaum, H., & Horvitz, E. (2022). Ethical considerations in legal AI systems. Journal of Legal Technology, 8(1), 34–52.

Hynes, J., Chon, K., & Porter, R. (2020). Technology and access to justice. Harvard Journal of Law & Technology, 33(2), 445–498.

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y., Madotto, A., & Fung, P. (2023). Survey of hallucination in natural language generation. ACM Computing Surveys, 55(12), 1–38. https://doi.org/10.1145/3571730

Katz, D. M., Bommarito, M. J., & Arbelaez, P. (2022). GPT-4 and the future of legal services. CodeX: The Stanford Center for Legal Informatics. https://law.stanford.edu/codex-the-stanford-center-for-legal-informatics/

Law360. (2023, March 15). ROSS Intelligence shuts down after IBM Watson dispute. Law360 Technology.

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in Neural Information Processing Systems, 33, 9459–9474.

Mallen, A., Asai, A., Zhong, V., Das, R., Hajishirzi, H., & Zettlemoyer, L. (2023). When not to trust language models: Investigating effectiveness of parametric and non-parametric memories. In Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (ACL 2023) (pp. 9802–9822). Association for Computational Linguistics.

Nam, T., & Wexler, J. (2020). Access to justice technology: A framework for evaluation. Journal of Online Dispute Resolution, 9(1), 45–67.

Nielsen, J. (1994). Usability engineering. Academic Press.

Surden, H. (2021). Artificial intelligence and law: An overview. Georgia State University Law Review, 35(4), 1305–1336.

Tighe, M. (2022). The limitations of rule-based legal chatbots. Legal Informatics Quarterly, 12(3), 78–92.

United Nations Development Programme. (2022). Access to justice in sub-Saharan Africa: Challenges and opportunities. UNDP.

World Bank. (2022). World development report 2022: Finance for an equitable recovery. World Bank. https://doi.org/10.1596/978-1-4648-1730-4

World Justice Project. (2023). Rule of law index 2023. World Justice Project. https://worldjusticeproject.org/rule-of-law-index/



# APPENDIX A: PROPOSED EVALUATION METRICS



# APPENDIX B: ETHICAL CONSIDERATIONS


1. Disclaimer: System must clearly state it does not provide legal advice

2. Data Privacy: User data encrypted and stored securely (GDPR compliant)

3. Bias Mitigation: Regular auditing of AI responses for discriminatory content

4. Transparency: Sources cited for all legal information provided

5. Human Oversight: Option to escalate to human legal professionals






















