--
-- PostgreSQL database dump
--

-- Dumped from database version 14.8 (Debian 14.8-1.pgdg120+1)
-- Dumped by pg_dump version 15.3 (Ubuntu 15.3-0ubuntu0.23.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: navigator
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO navigator;

--
-- Name: documentstatus; Type: TYPE; Schema: public; Owner: navigator
--

CREATE TYPE public.documentstatus AS ENUM (
    'CREATED',
    'PUBLISHED',
    'DELETED'
);


ALTER TYPE public.documentstatus OWNER TO navigator;

--
-- Name: eventstatus; Type: TYPE; Schema: public; Owner: navigator
--

CREATE TYPE public.eventstatus AS ENUM (
    'OK',
    'DUPLICATED'
);


ALTER TYPE public.eventstatus OWNER TO navigator;

--
-- Name: familycategory; Type: TYPE; Schema: public; Owner: navigator
--

CREATE TYPE public.familycategory AS ENUM (
    'EXECUTIVE',
    'LEGISLATIVE',
    'UNFCCC'
);


ALTER TYPE public.familycategory OWNER TO navigator;

--
-- Name: familystatus; Type: TYPE; Schema: public; Owner: navigator
--

CREATE TYPE public.familystatus AS ENUM (
    'CREATED',
    'PUBLISHED',
    'DELETED'
);


ALTER TYPE public.familystatus OWNER TO navigator;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO navigator;

--
-- Name: app_user; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.app_user (
    email character varying NOT NULL,
    name character varying,
    hashed_password character varying,
    is_superuser boolean NOT NULL
);


ALTER TABLE public.app_user OWNER TO navigator;

--
-- Name: collection; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.collection (
    import_id text NOT NULL,
    title text NOT NULL,
    description text NOT NULL
);


ALTER TABLE public.collection OWNER TO navigator;

--
-- Name: collection_family; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.collection_family (
    collection_import_id text NOT NULL,
    family_import_id text NOT NULL
);


ALTER TABLE public.collection_family OWNER TO navigator;

--
-- Name: collection_organisation; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.collection_organisation (
    collection_import_id text NOT NULL,
    organisation_id integer NOT NULL
);


ALTER TABLE public.collection_organisation OWNER TO navigator;

--
-- Name: family; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.family (
    title text NOT NULL,
    import_id text NOT NULL,
    description text NOT NULL,
    geography_id integer NOT NULL,
    family_category public.familycategory NOT NULL
);


ALTER TABLE public.family OWNER TO navigator;

--
-- Name: family_document; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.family_document (
    family_import_id text NOT NULL,
    physical_document_id integer NOT NULL,
    import_id text NOT NULL,
    variant_name text,
    document_status public.documentstatus NOT NULL,
    document_type text,
    document_role text
);


ALTER TABLE public.family_document OWNER TO navigator;

--
-- Name: family_document_role; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.family_document_role (
    name text NOT NULL,
    description text NOT NULL
);


ALTER TABLE public.family_document_role OWNER TO navigator;

--
-- Name: family_document_type; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.family_document_type (
    name text NOT NULL,
    description text NOT NULL
);


ALTER TABLE public.family_document_type OWNER TO navigator;

--
-- Name: family_event; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.family_event (
    import_id text NOT NULL,
    title text NOT NULL,
    date timestamp with time zone NOT NULL,
    event_type_name text NOT NULL,
    family_import_id text NOT NULL,
    family_document_import_id text,
    status public.eventstatus NOT NULL
);


ALTER TABLE public.family_event OWNER TO navigator;

--
-- Name: family_event_type; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.family_event_type (
    name text NOT NULL,
    description text NOT NULL
);


ALTER TABLE public.family_event_type OWNER TO navigator;

--
-- Name: family_metadata; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.family_metadata (
    family_import_id text NOT NULL,
    taxonomy_id integer NOT NULL,
    value jsonb NOT NULL
);


ALTER TABLE public.family_metadata OWNER TO navigator;

--
-- Name: family_organisation; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.family_organisation (
    family_import_id text NOT NULL,
    organisation_id integer NOT NULL
);


ALTER TABLE public.family_organisation OWNER TO navigator;

--
-- Name: geo_statistics; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.geo_statistics (
    id integer NOT NULL,
    name text NOT NULL,
    geography_id integer NOT NULL,
    legislative_process text NOT NULL,
    federal boolean NOT NULL,
    federal_details text NOT NULL,
    political_groups text NOT NULL,
    global_emissions_percent double precision,
    climate_risk_index double precision,
    worldbank_income_group text NOT NULL,
    visibility_status text NOT NULL
);


ALTER TABLE public.geo_statistics OWNER TO navigator;

--
-- Name: geo_statistics_id_seq; Type: SEQUENCE; Schema: public; Owner: navigator
--

CREATE SEQUENCE public.geo_statistics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.geo_statistics_id_seq OWNER TO navigator;

--
-- Name: geo_statistics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: navigator
--

ALTER SEQUENCE public.geo_statistics_id_seq OWNED BY public.geo_statistics.id;


--
-- Name: geography; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.geography (
    id integer NOT NULL,
    display_value text NOT NULL,
    value text,
    type text,
    parent_id integer,
    slug text NOT NULL
);


ALTER TABLE public.geography OWNER TO navigator;

--
-- Name: geography_id_seq; Type: SEQUENCE; Schema: public; Owner: navigator
--

CREATE SEQUENCE public.geography_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.geography_id_seq OWNER TO navigator;

--
-- Name: geography_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: navigator
--

ALTER SEQUENCE public.geography_id_seq OWNED BY public.geography.id;


--
-- Name: language; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.language (
    id integer NOT NULL,
    language_code character(3) NOT NULL,
    part1_code character(2),
    part2_code character(3),
    name text
);


ALTER TABLE public.language OWNER TO navigator;

--
-- Name: language_id_seq; Type: SEQUENCE; Schema: public; Owner: navigator
--

CREATE SEQUENCE public.language_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.language_id_seq OWNER TO navigator;

--
-- Name: language_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: navigator
--

ALTER SEQUENCE public.language_id_seq OWNED BY public.language.id;


--
-- Name: metadata_organisation; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.metadata_organisation (
    taxonomy_id integer NOT NULL,
    organisation_id integer NOT NULL
);


ALTER TABLE public.metadata_organisation OWNER TO navigator;

--
-- Name: metadata_taxonomy; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.metadata_taxonomy (
    id integer NOT NULL,
    description text NOT NULL,
    valid_metadata jsonb NOT NULL
);


ALTER TABLE public.metadata_taxonomy OWNER TO navigator;

--
-- Name: metadata_taxonomy_id_seq; Type: SEQUENCE; Schema: public; Owner: navigator
--

CREATE SEQUENCE public.metadata_taxonomy_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metadata_taxonomy_id_seq OWNER TO navigator;

--
-- Name: metadata_taxonomy_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: navigator
--

ALTER SEQUENCE public.metadata_taxonomy_id_seq OWNED BY public.metadata_taxonomy.id;


--
-- Name: organisation; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.organisation (
    id integer NOT NULL,
    name character varying,
    description character varying,
    organisation_type character varying
);


ALTER TABLE public.organisation OWNER TO navigator;

--
-- Name: organisation_admin; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.organisation_admin (
    appuser_email character varying NOT NULL,
    organisation_id integer NOT NULL,
    job_title character varying,
    is_active boolean NOT NULL,
    is_admin boolean NOT NULL
);


ALTER TABLE public.organisation_admin OWNER TO navigator;

--
-- Name: organisation_id_seq; Type: SEQUENCE; Schema: public; Owner: navigator
--

CREATE SEQUENCE public.organisation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.organisation_id_seq OWNER TO navigator;

--
-- Name: organisation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: navigator
--

ALTER SEQUENCE public.organisation_id_seq OWNED BY public.organisation.id;


--
-- Name: physical_document; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.physical_document (
    id integer NOT NULL,
    title text NOT NULL,
    md5_sum text,
    source_url text,
    content_type text,
    cdn_object text
);


ALTER TABLE public.physical_document OWNER TO navigator;

--
-- Name: physical_document_id_seq; Type: SEQUENCE; Schema: public; Owner: navigator
--

CREATE SEQUENCE public.physical_document_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.physical_document_id_seq OWNER TO navigator;

--
-- Name: physical_document_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: navigator
--

ALTER SEQUENCE public.physical_document_id_seq OWNED BY public.physical_document.id;


--
-- Name: physical_document_language; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.physical_document_language (
    language_id integer NOT NULL,
    document_id integer NOT NULL
);


ALTER TABLE public.physical_document_language OWNER TO navigator;

--
-- Name: slug; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.slug (
    name text NOT NULL,
    family_import_id text,
    family_document_import_id text,
    CONSTRAINT ck_slug__must_reference_exactly_one_entity CHECK ((num_nonnulls(family_import_id, family_document_import_id) = 1))
);


ALTER TABLE public.slug OWNER TO navigator;

--
-- Name: variant; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.variant (
    variant_name text NOT NULL,
    description text NOT NULL
);


ALTER TABLE public.variant OWNER TO navigator;

--
-- Name: geo_statistics id; Type: DEFAULT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.geo_statistics ALTER COLUMN id SET DEFAULT nextval('public.geo_statistics_id_seq'::regclass);


--
-- Name: geography id; Type: DEFAULT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.geography ALTER COLUMN id SET DEFAULT nextval('public.geography_id_seq'::regclass);


--
-- Name: language id; Type: DEFAULT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.language ALTER COLUMN id SET DEFAULT nextval('public.language_id_seq'::regclass);


--
-- Name: metadata_taxonomy id; Type: DEFAULT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.metadata_taxonomy ALTER COLUMN id SET DEFAULT nextval('public.metadata_taxonomy_id_seq'::regclass);


--
-- Name: organisation id; Type: DEFAULT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.organisation ALTER COLUMN id SET DEFAULT nextval('public.organisation_id_seq'::regclass);


--
-- Name: physical_document id; Type: DEFAULT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.physical_document ALTER COLUMN id SET DEFAULT nextval('public.physical_document_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.alembic_version (version_num) FROM stdin;
0017
\.


--
-- Data for Name: app_user; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.app_user (email, name, hashed_password, is_superuser) FROM stdin;
\.


--
-- Data for Name: collection; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.collection (import_id, title, description) FROM stdin;
\.


--
-- Data for Name: collection_family; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.collection_family (collection_import_id, family_import_id) FROM stdin;
\.


--
-- Data for Name: collection_organisation; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.collection_organisation (collection_import_id, organisation_id) FROM stdin;
\.


--
-- Data for Name: family; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.family (title, import_id, description, geography_id, family_category) FROM stdin;
\.


--
-- Data for Name: family_document; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.family_document (family_import_id, physical_document_id, import_id, variant_name, document_status, document_type, document_role) FROM stdin;
\.


--
-- Data for Name: family_document_role; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.family_document_role (name, description) FROM stdin;
\.


--
-- Data for Name: family_document_type; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.family_document_type (name, description) FROM stdin;
\.


--
-- Data for Name: family_event; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.family_event (import_id, title, date, event_type_name, family_import_id, family_document_import_id, status) FROM stdin;
\.


--
-- Data for Name: family_event_type; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.family_event_type (name, description) FROM stdin;
\.


--
-- Data for Name: family_metadata; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.family_metadata (family_import_id, taxonomy_id, value) FROM stdin;
\.


--
-- Data for Name: family_organisation; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.family_organisation (family_import_id, organisation_id) FROM stdin;
\.


--
-- Data for Name: geo_statistics; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.geo_statistics (id, name, geography_id, legislative_process, federal, federal_details, political_groups, global_emissions_percent, climate_risk_index, worldbank_income_group, visibility_status) FROM stdin;
\.


--
-- Data for Name: geography; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.geography (id, display_value, value, type, parent_id, slug) FROM stdin;
\.


--
-- Data for Name: language; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.language (id, language_code, part1_code, part2_code, name) FROM stdin;
\.


--
-- Data for Name: metadata_organisation; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.metadata_organisation (taxonomy_id, organisation_id) FROM stdin;
\.


--
-- Data for Name: metadata_taxonomy; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.metadata_taxonomy (id, description, valid_metadata) FROM stdin;
\.


--
-- Data for Name: organisation; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.organisation (id, name, description, organisation_type) FROM stdin;
\.


--
-- Data for Name: organisation_admin; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.organisation_admin (appuser_email, organisation_id, job_title, is_active, is_admin) FROM stdin;
\.


--
-- Data for Name: physical_document; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.physical_document (id, title, md5_sum, source_url, content_type, cdn_object) FROM stdin;
\.


--
-- Data for Name: physical_document_language; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.physical_document_language (language_id, document_id) FROM stdin;
\.


--
-- Data for Name: slug; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.slug (name, family_import_id, family_document_import_id) FROM stdin;
\.


--
-- Data for Name: variant; Type: TABLE DATA; Schema: public; Owner: navigator
--

COPY public.variant (variant_name, description) FROM stdin;
\.


--
-- Name: geo_statistics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: navigator
--

SELECT pg_catalog.setval('public.geo_statistics_id_seq', 1, false);


--
-- Name: geography_id_seq; Type: SEQUENCE SET; Schema: public; Owner: navigator
--

SELECT pg_catalog.setval('public.geography_id_seq', 1, false);


--
-- Name: language_id_seq; Type: SEQUENCE SET; Schema: public; Owner: navigator
--

SELECT pg_catalog.setval('public.language_id_seq', 1, false);


--
-- Name: metadata_taxonomy_id_seq; Type: SEQUENCE SET; Schema: public; Owner: navigator
--

SELECT pg_catalog.setval('public.metadata_taxonomy_id_seq', 1, false);


--
-- Name: organisation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: navigator
--

SELECT pg_catalog.setval('public.organisation_id_seq', 1, false);


--
-- Name: physical_document_id_seq; Type: SEQUENCE SET; Schema: public; Owner: navigator
--

SELECT pg_catalog.setval('public.physical_document_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: app_user pk_app_user; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT pk_app_user PRIMARY KEY (email);


--
-- Name: collection pk_collection; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.collection
    ADD CONSTRAINT pk_collection PRIMARY KEY (import_id);


--
-- Name: collection_family pk_collection_family; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.collection_family
    ADD CONSTRAINT pk_collection_family PRIMARY KEY (collection_import_id, family_import_id);


--
-- Name: collection_organisation pk_collection_organisation; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.collection_organisation
    ADD CONSTRAINT pk_collection_organisation PRIMARY KEY (collection_import_id);


--
-- Name: family pk_family; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family
    ADD CONSTRAINT pk_family PRIMARY KEY (import_id);


--
-- Name: family_document pk_family_document; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_document
    ADD CONSTRAINT pk_family_document PRIMARY KEY (import_id);


--
-- Name: family_document_role pk_family_document_role; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_document_role
    ADD CONSTRAINT pk_family_document_role PRIMARY KEY (name);


--
-- Name: family_document_type pk_family_document_type; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_document_type
    ADD CONSTRAINT pk_family_document_type PRIMARY KEY (name);


--
-- Name: family_event pk_family_event; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_event
    ADD CONSTRAINT pk_family_event PRIMARY KEY (import_id);


--
-- Name: family_event_type pk_family_event_type; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_event_type
    ADD CONSTRAINT pk_family_event_type PRIMARY KEY (name);


--
-- Name: family_metadata pk_family_metadata; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_metadata
    ADD CONSTRAINT pk_family_metadata PRIMARY KEY (family_import_id, taxonomy_id);


--
-- Name: family_organisation pk_family_organisation; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_organisation
    ADD CONSTRAINT pk_family_organisation PRIMARY KEY (family_import_id);


--
-- Name: geo_statistics pk_geo_statistics; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.geo_statistics
    ADD CONSTRAINT pk_geo_statistics PRIMARY KEY (id);


--
-- Name: geography pk_geography; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.geography
    ADD CONSTRAINT pk_geography PRIMARY KEY (id);


--
-- Name: language pk_language; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.language
    ADD CONSTRAINT pk_language PRIMARY KEY (id);


--
-- Name: metadata_organisation pk_metadata_organisation; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.metadata_organisation
    ADD CONSTRAINT pk_metadata_organisation PRIMARY KEY (organisation_id);


--
-- Name: metadata_taxonomy pk_metadata_taxonomy; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.metadata_taxonomy
    ADD CONSTRAINT pk_metadata_taxonomy PRIMARY KEY (id);


--
-- Name: organisation pk_organisation; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.organisation
    ADD CONSTRAINT pk_organisation PRIMARY KEY (id);


--
-- Name: organisation_admin pk_organisation_admin; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.organisation_admin
    ADD CONSTRAINT pk_organisation_admin PRIMARY KEY (appuser_email, organisation_id);


--
-- Name: physical_document pk_physical_document; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.physical_document
    ADD CONSTRAINT pk_physical_document PRIMARY KEY (id);


--
-- Name: physical_document_language pk_physical_document_language; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.physical_document_language
    ADD CONSTRAINT pk_physical_document_language PRIMARY KEY (language_id, document_id);


--
-- Name: slug pk_slug; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.slug
    ADD CONSTRAINT pk_slug PRIMARY KEY (name);


--
-- Name: variant pk_variant; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.variant
    ADD CONSTRAINT pk_variant PRIMARY KEY (variant_name);


--
-- Name: family_document uq_family_document__physical_document_id; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_document
    ADD CONSTRAINT uq_family_document__physical_document_id UNIQUE (physical_document_id);


--
-- Name: geo_statistics uq_geo_statistics__name; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.geo_statistics
    ADD CONSTRAINT uq_geo_statistics__name UNIQUE (name);


--
-- Name: geography uq_geography__display_value; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.geography
    ADD CONSTRAINT uq_geography__display_value UNIQUE (display_value);


--
-- Name: language uq_language__language_code; Type: CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.language
    ADD CONSTRAINT uq_language__language_code UNIQUE (language_code);


--
-- Name: ix_geography_slug; Type: INDEX; Schema: public; Owner: navigator
--

CREATE UNIQUE INDEX ix_geography_slug ON public.geography USING btree (slug);


--
-- Name: collection_family fk_collection_family__collection_import_id__collection; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.collection_family
    ADD CONSTRAINT fk_collection_family__collection_import_id__collection FOREIGN KEY (collection_import_id) REFERENCES public.collection(import_id);


--
-- Name: collection_family fk_collection_family__family_import_id__family; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.collection_family
    ADD CONSTRAINT fk_collection_family__family_import_id__family FOREIGN KEY (family_import_id) REFERENCES public.family(import_id);


--
-- Name: collection_organisation fk_collection_organisation__collection_import_id__collection; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.collection_organisation
    ADD CONSTRAINT fk_collection_organisation__collection_import_id__collection FOREIGN KEY (collection_import_id) REFERENCES public.collection(import_id);


--
-- Name: collection_organisation fk_collection_organisation__organisation_id__organisation; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.collection_organisation
    ADD CONSTRAINT fk_collection_organisation__organisation_id__organisation FOREIGN KEY (organisation_id) REFERENCES public.organisation(id);


--
-- Name: family fk_family__geography_id__geography; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family
    ADD CONSTRAINT fk_family__geography_id__geography FOREIGN KEY (geography_id) REFERENCES public.geography(id);


--
-- Name: family_document fk_family_document__document_role__family_document_role; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_document
    ADD CONSTRAINT fk_family_document__document_role__family_document_role FOREIGN KEY (document_role) REFERENCES public.family_document_role(name);


--
-- Name: family_document fk_family_document__document_type__family_document_type; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_document
    ADD CONSTRAINT fk_family_document__document_type__family_document_type FOREIGN KEY (document_type) REFERENCES public.family_document_type(name);


--
-- Name: family_document fk_family_document__family_import_id__family; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_document
    ADD CONSTRAINT fk_family_document__family_import_id__family FOREIGN KEY (family_import_id) REFERENCES public.family(import_id);


--
-- Name: family_document fk_family_document__physical_document_id__physical_document; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_document
    ADD CONSTRAINT fk_family_document__physical_document_id__physical_document FOREIGN KEY (physical_document_id) REFERENCES public.physical_document(id);


--
-- Name: family_document fk_family_document__variant_name__variant; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_document
    ADD CONSTRAINT fk_family_document__variant_name__variant FOREIGN KEY (variant_name) REFERENCES public.variant(variant_name);


--
-- Name: family_event fk_family_event__event_type_name__family_event_type; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_event
    ADD CONSTRAINT fk_family_event__event_type_name__family_event_type FOREIGN KEY (event_type_name) REFERENCES public.family_event_type(name);


--
-- Name: family_event fk_family_event__family_document_import_id__family_document; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_event
    ADD CONSTRAINT fk_family_event__family_document_import_id__family_document FOREIGN KEY (family_document_import_id) REFERENCES public.family_document(import_id);


--
-- Name: family_event fk_family_event__family_import_id__family; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_event
    ADD CONSTRAINT fk_family_event__family_import_id__family FOREIGN KEY (family_import_id) REFERENCES public.family(import_id);


--
-- Name: family_metadata fk_family_metadata__family_import_id__family; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_metadata
    ADD CONSTRAINT fk_family_metadata__family_import_id__family FOREIGN KEY (family_import_id) REFERENCES public.family(import_id);


--
-- Name: family_metadata fk_family_metadata__taxonomy_id__metadata_taxonomy; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_metadata
    ADD CONSTRAINT fk_family_metadata__taxonomy_id__metadata_taxonomy FOREIGN KEY (taxonomy_id) REFERENCES public.metadata_taxonomy(id);


--
-- Name: family_organisation fk_family_organisation__family_import_id__family; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_organisation
    ADD CONSTRAINT fk_family_organisation__family_import_id__family FOREIGN KEY (family_import_id) REFERENCES public.family(import_id);


--
-- Name: family_organisation fk_family_organisation__organisation_id__organisation; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.family_organisation
    ADD CONSTRAINT fk_family_organisation__organisation_id__organisation FOREIGN KEY (organisation_id) REFERENCES public.organisation(id);


--
-- Name: geo_statistics fk_geo_statistics__geography_id__geography; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.geo_statistics
    ADD CONSTRAINT fk_geo_statistics__geography_id__geography FOREIGN KEY (geography_id) REFERENCES public.geography(id);


--
-- Name: geography fk_geography__parent_id__geography; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.geography
    ADD CONSTRAINT fk_geography__parent_id__geography FOREIGN KEY (parent_id) REFERENCES public.geography(id);


--
-- Name: metadata_organisation fk_metadata_organisation__organisation_id__organisation; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.metadata_organisation
    ADD CONSTRAINT fk_metadata_organisation__organisation_id__organisation FOREIGN KEY (organisation_id) REFERENCES public.organisation(id);


--
-- Name: metadata_organisation fk_metadata_organisation__taxonomy_id__metadata_taxonomy; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.metadata_organisation
    ADD CONSTRAINT fk_metadata_organisation__taxonomy_id__metadata_taxonomy FOREIGN KEY (taxonomy_id) REFERENCES public.metadata_taxonomy(id);


--
-- Name: organisation_admin fk_organisation_admin__appuser_email__app_user; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.organisation_admin
    ADD CONSTRAINT fk_organisation_admin__appuser_email__app_user FOREIGN KEY (appuser_email) REFERENCES public.app_user(email);


--
-- Name: organisation_admin fk_organisation_admin__organisation_id__organisation; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.organisation_admin
    ADD CONSTRAINT fk_organisation_admin__organisation_id__organisation FOREIGN KEY (organisation_id) REFERENCES public.organisation(id);


--
-- Name: physical_document_language fk_physical_document_language__document_id__physical_document; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.physical_document_language
    ADD CONSTRAINT fk_physical_document_language__document_id__physical_document FOREIGN KEY (document_id) REFERENCES public.physical_document(id) ON DELETE CASCADE;


--
-- Name: physical_document_language fk_physical_document_language__language_id__language; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.physical_document_language
    ADD CONSTRAINT fk_physical_document_language__language_id__language FOREIGN KEY (language_id) REFERENCES public.language(id);


--
-- Name: slug fk_slug__family_document_import_id__family_document; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.slug
    ADD CONSTRAINT fk_slug__family_document_import_id__family_document FOREIGN KEY (family_document_import_id) REFERENCES public.family_document(import_id);


--
-- Name: slug fk_slug__family_import_id__family; Type: FK CONSTRAINT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.slug
    ADD CONSTRAINT fk_slug__family_import_id__family FOREIGN KEY (family_import_id) REFERENCES public.family(import_id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: navigator
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: entity_counter; Type: TABLE; Schema: public; Owner: navigator
--

CREATE TABLE public.entity_counter (
    id integer NOT NULL,
    description character varying NOT NULL,
    prefix character varying NOT NULL,
    counter integer,
    CONSTRAINT ck_entity_counter__prefix_allowed_orgs CHECK (((prefix)::text = ANY ((ARRAY['CCLW'::character varying, 'UNFCCC'::character varying])::text[])))
);


ALTER TABLE public.entity_counter OWNER TO navigator;

--
-- Name: entity_counter_id_seq; Type: SEQUENCE; Schema: public; Owner: navigator
--

CREATE SEQUENCE public.entity_counter_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.entity_counter_id_seq OWNER TO navigator;

--
-- Name: entity_counter_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: navigator
--

ALTER SEQUENCE public.entity_counter_id_seq OWNED BY public.entity_counter.id;


--
-- Name: entity_counter id; Type: DEFAULT; Schema: public; Owner: navigator
--

ALTER TABLE ONLY public.entity_counter ALTER COLUMN id SET DEFAULT nextval('public.entity_counter_id_seq'::regclass);


--
-- PostgreSQL database dump complete
--

