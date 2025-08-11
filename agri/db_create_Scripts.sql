-- public.usda_weekly_export_sales definition

-- Drop table

-- DROP TABLE public.usda_weekly_export_sales;

CREATE TABLE public.usda_weekly_export_sales (
	"index" int8 NULL,
	"commodityCode" int8 NULL,
	"countryCode" int8 NULL,
	"weeklyExports" int8 NULL,
	"accumulatedExports" int8 NULL,
	"outstandingSales" int8 NULL,
	"grossNewSales" int8 NULL,
	"currentMYNetSales" int8 NULL,
	"currentMYTotalCommitment" int8 NULL,
	"nextMYOutstandingSales" int8 NULL,
	"nextMYNetSales" int8 NULL,
	"unitId" int8 NULL,
	"weekEndingDate" text NULL,
	market_year int8 NULL,
	CONSTRAINT usda_weekly_export_sales_commodities_fk FOREIGN KEY ("commodityCode") REFERENCES public.commodities("commodityCode"),
	CONSTRAINT usda_weekly_export_sales_countries_fk FOREIGN KEY ("countryCode") REFERENCES public.countries("countryCode")
);
CREATE INDEX ix_usda_weekly_export_sales_index ON public.usda_weekly_export_sales USING btree (index);

-- public.countries definition

-- Drop table

-- DROP TABLE public.countries;

CREATE TABLE public.countries (
	"index" int8 NULL,
	"countryCode" int8 NULL,
	"countryName" text NULL,
	"countryDescription" text NULL,
	"regionId" int8 NULL,
	"gencCode" text NULL,
	CONSTRAINT countries_unique UNIQUE ("countryCode")
);
CREATE INDEX ix_countries_index ON public.countries USING btree (index);

-- public.commodities definition

-- Drop table

-- DROP TABLE public.commodities;

CREATE TABLE public.commodities (
	"index" int8 NULL,
	"commodityCode" int8 NULL,
	"commodityName" text NULL,
	"unitId" int8 NULL,
	CONSTRAINT commodities_unique UNIQUE ("commodityCode")
);
CREATE INDEX ix_commodities_index ON public.commodities USING btree (index);