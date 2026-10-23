<root>
<layer name="blitz350_tspender" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_blitz_categorytext" >
  <config>
    <event id="Ts1HappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_ts-350_b_201803.jpg"/>
    <label text="be_blitz350ts_content" position="content1" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c424bd9ce0d07bafd33f4abbdd607bf6"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blitz400_tspender" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_blitz_categorytext" >
  <config>
    <event id="Ts2HappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_ts_400_b_201901.jpg"/>
    <label text="be_blitz400ts_content" position="content1" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=da5ad9e351438e0baf506d457cbe33b8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blitz400" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_blitz_categorytext" >
  <config>
    <event id="UltraHappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_400_b_201803.jpg"/>
    <label text="be_blitz400_content" position="content1" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=30d8bc761397b775b6e6f80712b8bb56"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blitz400_ts3spender" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_blitz_categorytext" >
  <config>
    <event id="Ts3HappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_ts_400_b_201901.jpg"/>
    <label text="be_blitz400ts_content" position="content1" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5b4dbd0471622a8c11e6fd0636ac98f0"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blitz350" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_blitz_categorytext" >
  <config>
    <event id="GigaHappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_350_b_201803.jpg"/>
    <label text="be_blitz350_content" position="content1" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7fb4638e8489d00e76385500816e077a"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mega_happyhour" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_mega_happyhour_categorytext" >
  <config>
    <event id="MegaHappyHour"/>
  </config>
  <assignments>
    <background assetID="mhh_b_201803.jpg"/>
    <label text="be_megahappyhour_content" position="content1" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=b028ac35cc5f77c7ec149d6002b661fb"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blitz400_tspenderLast" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_blitz_categorytext" >
  <config>
      </config>
  <assignments>
    <background assetID="ghh_ts_400_last_chance_b_201803.jpg"/>
    <label text="be_blitz400tsLast_content" position="content1" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=da5ad9e351438e0baf506d457cbe33b8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blitz300_tsABR" prio="0" countdown ="1" category = "news" categoryOverrideKey="bn_blitz_categorytext" >
  <config>
    <event id="TsABRMegaHappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_ts_300_v06_b_201911.jpg"/>
    <label text="be_blitz300tsABR_content" position="content1" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a58a5ff1d93645a369e52ca0f7180297"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blitz400_tsULF4spender" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_blitz_categorytext" >
  <config>
    <event id="TsULF4HappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_tsULF4_400_b_2019.jpg"/>
    <label text="be_blitz400tsULF4_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2e6c7e965632603c66df8629e45bbcf6"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blitz400_tsFS3spender" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_blitz_categorytext" >
  <config>
    <event id="TsFS3HappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_tsFS3_400_b_2019.jpg"/>
    <label text="be_blitz400tsFS3_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1aebba22452fc152558a0db021268480"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="happyhour" prio="0" countdown ="1" category = "sales" categoryOverrideKey="bn_happyhour_categorytext" >
  <config>
    <event id="HappyHour"/>
  </config>
  <assignments>
    <background assetID="hh_b_201803.jpg"/>
    <label text="be_happyhour_content" position="content1" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3b06ceb9d7623b410b08dfcda1fe4778"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202001" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202001.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJan2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="captainDec2022" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202212_CaptainSystem.jpg"/>
    <label text="bn_captainDec22_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_captainDec22_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=bee8be46cdd28aaa8d5be83a055d2d53"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="summermini2022" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Summer_Mini_Event_2022.jpg"/>
    <label text="bn_summermini2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_summermini2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=669ae8125fe143a50ae069c8d460e806"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202606" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202606.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Jun2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="petExpansionSep2022" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_petExpansionSep2022.jpg"/>
    <label text="bn_petExpansionSep2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_petExpansionSep2022_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e5ecc4ce8529e472c8022e23f64db92e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="shipPlusFeb2022" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_shipupgradenov2022.jpg"/>
    <label text="bn_shipupgradenov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_shipupgradenov2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fdb368ce3b0f89c9752d17219f3759bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianJun2023" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202306.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianJune2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_may2021" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202105_breakingnews.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocMay2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202508" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202508.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Aug2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_may2023" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202305.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocMay2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="starterpack_regular" prio="1" countdown ="1" category = "deals">
  <config>
  </config>
  <assignments>
    <background assetID="starterpack_s_201802.jpg"/>
    <label text="bn_starter_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_starter_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="DEPRECATED"  position="center">
    </button>
  </actions>
</layer>

<layer name="shipPlusAug2022" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_shipupgradeaug2022.jpg"/>
    <label text="bn_shipupgradenov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_shipupgradeaug2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a3e29d80e4e81815ac088ae2925dcb70"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidian_202312" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202312.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianDec2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_Nov2023" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_Nov2023.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Nov2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2aeff0b8335da034af76f9d1d1e9d89f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202510" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202510_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbOct2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="hitacAssault_202508" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_hitacAssault_202508.jpg"/>
    <label text="bn_hitacAssault_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_hitacassault202508_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7503b7d45fd337deee4ec5d8a0bc4dbd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="bootyReworkAug2020" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="green_booty_rework_breakingnews_202008.png"/>
    <label text="bn_greenBootyUpdate_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_greenBootyUpdate_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="obsidian202606" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202606.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianJune2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianJun2022" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202206_breakingnews.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianJune2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202010" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202010_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbOct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202310" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202310_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbOct2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battlePass_mimesisMutiny" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass-escort_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=21424063184f715f1c13bde76247ed90"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="Double_Honor_and_XP_Day" prio="1" countdown ="1" category = "events">
  <config>
  </config>
  <assignments>
    <background assetID="honor-xp-day_s_201802.jpg"/>
    <label text="bn_doublexpday_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_doublexpday_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="higher_button">
      <onclick>
        <link href="?action=internalPayment"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galaxy_gate_double_reward" prio="1" countdown ="1" category = "events" >
  <config>
    <event id="GalaxyGateDay"/>
  </config>
  <assignments>
    <background assetID="gg_double-reward-day_s_201802.jpg"/>
    <label text="bn_ggDouble_headline" position="half_headline" style="headline"/>
    <label text="bn_ggDouble_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_ggAction_button"  position="center">
      <onclick>
        <link href="?action=internalGalaxyGates"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="ggDoubleWeek" prio="1" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="gg_week_201809.jpg"/>
    <label text="bn_ggDoubleWeek_headline" position="half_headline" style="headline"/>
    <label text="bn_ggDoubleWeek_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_ggAction_button"  position="center">
      <onclick>
        <link href="?action=internalGalaxyGates"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianMar2022" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_obsidian202112.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianMarch2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianSep2022" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202209.jpg"/>
    <label text="bn_obsidianSep2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianSep2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianJun2020" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202006_breaking_news.jpg"/>
    <label text="bn_obsidianSep2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianJun2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="BE_rnb_rework_202410" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202410_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbOct2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chinesenewyearjan2022" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chinesenewyearjan2022.jpg"/>
    <label text="bn_prosperous2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_prosperous2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=749409e31e062c48a55711c568c1008e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galaxy_gate_bonus_reward" prio="1" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="gg_bonus-reward-day-materializer_s_201802.jpg"/>
    <label text="bn_ggBonus_headline" position="half_headline" style="headline"/>
    <label text="bn_ggBonus_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_ggAction_button"  position="center">
      <onclick>
        <link href="?action=internalGalaxyGates"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="goalrush202416" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_goalrush_16.jpg"/>
    <label text="bn_goalrush_2024_1_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_goalrush_2024_1_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1de2558ec1134d5dfafceb9adfd7dcf7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chinesenewyearfeb2024" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_prosperousFeb2024.jpg"/>
    <label text="bn_prosperous2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_prosperous2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=749409e31e062c48a55711c568c1008e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202307" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_2307_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJul2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianDec2019" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_201912.jpg"/>
    <label text="bn_obsidianSep2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianDec2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="dispatchDay" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_dispatchDay.png"/>
    <label text="bn_dispatchDay_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_dispatchDay_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="sale_gearup" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gearUpDeals.png"/>
    <label text="bn_gearupDeals2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gearupDeals2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e7a22c9185483bf68628a8282cab3c90"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_Aug2023" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_Sep2023.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Aug2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2aeff0b8335da034af76f9d1d1e9d89f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="goalrush2024spain" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_goalrush_spain.jpg"/>
    <label text="bn_goalrush_2024_1_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_goalrush_2024_1_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1de2558ec1134d5dfafceb9adfd7dcf7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="50cent_deal" prio="1" countdown ="1" category = "deals">
  <config>
  </config>
  <assignments>
    <background assetID="50cent-booster_s_201803.jpg"/>
    <label text="bn_50cent_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_50cent_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=eba2ed4ab3bee6555ae5abc8d42100cc"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_feb2021" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202102_breakingnews.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocFeb2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202504" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202401_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJan2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202510" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202510.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Oct2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidian202409" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202409.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianSeptember2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202007" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202007.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJul2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202506" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202506.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Jun2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=321675672ad179de1eb9f7c85f111d95"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="perseusGrace202609" prio="1" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_PerseusGrace_202509.jpg"/>
    <label text="bn_perseusgrace2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_perseusgrace2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=87c0d0f083d45b1470c149d13b7fcb36"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="halloweenShopDiscount2018" prio="1" countdown ="1" category = "sales" >
  <config>
  </config>
  <assignments>
    <background assetID="sale_halloween_voucher_201810.jpg"/>
    <label text="bn_halloweenShopDiscount_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_halloweenShopDiscount_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="gauntletofPlutusJul2023" prio="1" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gauntletOfPlutusJul2023.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutusJul2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightExpansion" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="blacklight_s_201810.jpg"/>
    <label text="bn_blacklightExpansion_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightExpansion_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="clientcalendarbonus" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GoP_mini_calendar.jpg"/>
    <label text="bn_clientcalendar_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendar-8d_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="apoc_refresh_nov2023" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202311.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocNov2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="trRamadan2018" prio="1" countdown ="0" category = "sales" >
  <config>
  </config>
  <assignments>
    <background assetID="ramazan_2018_news.jpg"/>
    <label text="bn_trRamadan2018_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_trRamadan2018_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=53b5ec1d83d5a71baad4a1cab6e6d2ed"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202301" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202301_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJan2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_feb2024" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202302.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocFeb2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202610" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202610_303x168.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Oct2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="prometheusDay" prio="1" countdown ="1" category = "sales" >
  <config>
  </config>
  <assignments>
    <background assetID="prometheus_s_201811.jpg"/>
    <label text="bn_prometheusDay_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_prometheusDay_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a13806e7e450f9c6cc241eb078480fac"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="demaner" prio="1" countdown ="0" category = "news" >
  <config>
    <event id="DemanerHuntReocurring"/>
  </config>
  <assignments>
    <background assetID="demaner_s_201802.jpg"/>
    <label text="bn_demaner_headline" position="half_headline" style="headline"/>
    <label text="bn_demaner_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f2329246a06a6bfcc9522a1bbc2dc83c"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_201907" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_201907.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJul2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="trPriceSpecial2018" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="trPriceSpecial2018.jpg"/>
    <label text="bn_trPriceSpecial2018_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_trPriceSpecial2018_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_may2022" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202205_breakingnews.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocMay2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianDec2021" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_obsidian202112_blaze.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianDec2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="starterpack_ee" prio="1" countdown ="1" category = "deals">
  <config>
  </config>
  <assignments>
    <background assetID="starterpack-ee_s_201802.jpg"/>
    <label text="bn_starteree_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_starteree_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=b5157f787346718b6121909a546c7ba2"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianSep2020" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202009.png"/>
    <label text="bn_obsidianSep2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianSep2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="preblacklightnov2020" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_preblacklightnov2020.png"/>
    <label text="bn_preblacklightnov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_preblacklightnov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="shipPlusNov2021" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_upgradeship2021.jpg"/>
    <label text="bn_shipupgradenov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_shipupgradenov2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fdb368ce3b0f89c9752d17219f3759bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202210" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202210_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbOct2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battlePass_gop" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass-gop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c6e87f7e3269fdb9f5b7476a5626d8bb"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chinesenewyear202602" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_prosperous202602.jpg"/>
    <label text="bn_prosperous2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_prosperous2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=749409e31e062c48a55711c568c1008e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="goalrush20248" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_goalrush_08.jpg"/>
    <label text="bn_goalrush_2024_1_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_goalrush_2024_1_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1de2558ec1134d5dfafceb9adfd7dcf7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_Nov2022" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrianMarchNov2022.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrianNov2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3140951b959fdea77b0ff985b9592996"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendar202506" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202506_MiniCalendar.jpg"/>
    <label text="bn_clientcalendar_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendar-8d_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="rnb_rework_202607" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202607_breakingnews_303x168.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJul2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_202508" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202508.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocAugust2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="Synthesize" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_CannonIntensify_2025.jpg"/>
    <label text="bn_Synthesize_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_Synthesize_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5893e3c06de6860bb03529f816b140b2"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202411" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_Nov2024.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Nov2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="shipPlusDec2023" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Ship_Plus_Batch_7.jpg"/>
    <label text="bn_shipupgradenov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_shipupgradedec2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fdb368ce3b0f89c9752d17219f3759bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidian202512" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202512.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianDec2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_feb2022" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202202_breakingnews.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocFeb2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_Feb2020" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202002.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocFeb2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianJun2021" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202106_breakingnews.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianJun2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="ArmoryUnlock202512" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ParticleCannonRelease202512.jpg"/>
    <label text="bn_ParticleCannonRelease_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_ParticleCannonRelease_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5893e3c06de6860bb03529f816b140b2"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_nov2021" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202111_breakingnews.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocNov2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianDec2020" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202012_breakingnews.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianDec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="red_and_blue_bk_news" prio="1" countdown ="1" category = "deals" >
  <config>
      </config>
  <assignments>
    <background assetID="bbox_rb_s_201907.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJul2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianMay2019" prio="1" countdown ="1" category = "deals" >
  <config>
   </config>
  <assignments>
    <background assetID="obsidian_box_2019_04_breaking_news.jpg"/>
    <label text="bn_obsidianMay2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianMay2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_Jun2023" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_Jun2023_new.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrianJun2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2aeff0b8335da034af76f9d1d1e9d89f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chinesenewyear202402" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_prosperousFeb2024.jpg"/>
    <label text="bn_prosperous2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_prosperous2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=749409e31e062c48a55711c568c1008e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="halloweenoct2025" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Halloween2025.jpg"/>
    <label text="bn_halloweenoct2020_headline" position="half_headline" style="headline"/>
    <label text="bn_halloweenoct2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f3fb399b05e63e34c2c79cbce0a9efc6"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="dispatchSales" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_contentexpansion_202106.jpg"/>
    <label text="bn_dispatchSales_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_dispatchUpdateApr2022_content-v3" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=812430ba34b9c7d31b9700ab316a044c"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="amazonPrimeEn" prio="1" countdown ="0" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="amazon_prime_en_b_201806.jpg"/>
  </assignments>
  <actions>
    <button style="invisible_full_size_overlay"  text="bn_empty"  position="full_size">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=0ff9a2c205a58869a0a12b6bdd62ce21"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="dispatchExpansion202204" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_contentexpansion_202106.jpg"/>
    <label text="bn_contentexpansion202106_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_dispatchUpdateApr2022_content-v3" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=812430ba34b9c7d31b9700ab316a044c"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_202505" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202505.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocMay2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendarsep2022" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrianCalendar_2022.jpg"/>
    <label text="bn_autumncalendarsep2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_autumncalendarsep2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="battle_for_influence" prio="1" countdown ="1" category = "events">
  <config>
    <event id="InfluenceBattle"/>
  </config>
  <assignments>
    <background assetID="battle-for-influence_s_201802.jpg"/>
    <label text="bn_battleforinfluence_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battleforinfluence_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="battlePass_hitac" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass-hitac_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_aug2021" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202108_breakingnews.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocAug2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unstableExpansion2021" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_unstableExpansion2021.jpg"/>
    <label text="bn_unstableExpansion2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unstableExpansion2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="rnb_rework_202004" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202004_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbApr2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianSep2019" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_201907.jpg"/>
    <label text="bn_obsidianSep2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianSep2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="halloweenoct2022" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_halloweenoct2022.jpg"/>
    <label text="bn_halloweenoct2020_headline" position="half_headline" style="headline"/>
    <label text="bn_halloweenoct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5f57d6b747dc1584d66efa6dcd594261"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202511" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202511.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Nov2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="petExpansionSep2020" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_petExpansion.jpg"/>
    <label text="bn_petExpansionSep2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_petExpansionSep2020_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="empyrian_20260612" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202606.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Jun2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=321675672ad179de1eb9f7c85f111d95"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="halloweenoct2024" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Halloween2024.jpg"/>
    <label text="bn_halloweenoct2020_headline" position="half_headline" style="headline"/>
    <label text="bn_halloweenoct2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f3fb399b05e63e34c2c79cbce0a9efc6"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="premium_sale" prio="1" countdown ="0" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="premium_s_201802.jpg"/>
    <label text="bn_premiumsale_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_premiumsale_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalPayment"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="hitacAssault_202308" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_hitacAssault_202308_venomfix.jpg"/>
    <label text="bn_hitacAssault_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_hitacassault202308_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=80e4b14e1d09b491bf72dc2f7806b403"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202201" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202201_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJan2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_Mar2023" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrianMarchMarch2023.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrianMar2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=487f3345778bba022151da928a244e0d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_aug2022" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202208.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocAug2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unstableExpansionAug2022" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_umexpansionAug22.jpg"/>
    <label text="bn_unstableExpansion-aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unstableExpansion-aug2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a3b9f8953813e2e8f5d8336418c086e7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_Aug2020" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202008_breakingnews.png"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocAug2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202104" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202104_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbApr2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="autumnmini2022" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrianMarch.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrianMarch2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3140951b959fdea77b0ff985b9592996"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202503" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202503.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Mar2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=321675672ad179de1eb9f7c85f111d95"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_feb2023" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202302.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocFeb2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="halloweenoct2023" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_halloweenoct2023.jpg"/>
    <label text="bn_halloweenoct2020_headline" position="half_headline" style="headline"/>
    <label text="bn_halloweenoct2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5f57d6b747dc1584d66efa6dcd594261"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battlePass_plague" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass-plague_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d28a41589e8cbcfa7cda500132b96973"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_nov2020" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202011_breakingnews.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocNov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="ee_update_deals" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="extra_energy_deal_2019.jpg"/>
    <label text="bn_extraEnergyRefresh_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_extraEnergyRefresh_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a4191430006747226027fa1588095125"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="poc_refresh_202411" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202402.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocFeb2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battle_for_influence_EIC" prio="1" countdown ="1" category = "events">
  <config>
  </config>
  <assignments>
    <background assetID="faction_eic_s_201802.jpg"/>
    <label text="bn_battleforinfluenceEIC_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battleforinfluenceEIC_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="rnb_rework_202110" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202110_breakingnews.png"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbOct2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battle_for_influence_MMO" prio="1" countdown ="1" category = "events">
  <config>
  </config>
  <assignments>
    <background assetID="faction_mmo_s_201802.jpg"/>
    <label text="bn_battleforinfluenceMMO_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battleforinfluenceMMO_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="NewHitacBoosters2022" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_newBoostersSep2022.jpg"/>
    <label text="bn_newBoosters2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_newBoosters2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f09d4acbc9be89701ffbb3237fd7d27e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="XP_Day" prio="1" countdown ="1" category = "events" >
  <config>
    <event id="50percentBoosterEvent"/>
  </config>
  <assignments>
    <background assetID="xp-day_s_201802.jpg"/>
    <label text="bn_xpday_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_xpday_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalPayment"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="captainmay23" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_captainmay23.jpg"/>
    <label text="bn_captainmay23_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_captainmay23_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=0dbddd8e19c47ae7c412a0a1b179a69b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202408" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_Aug2024.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Aug2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="alienTechDevolarium" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="alien_tech_devolarium_s_201807.jpg"/>
    <label text="bn_alienTechDevolarium_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_alienTechDevolarium_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=8776aed568eff6d9d5325eec6c4c4cc9"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="halloweenoct2024unity" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Halloween2024.jpg"/>
    <label text="bn_halloweenoct2020_headline" position="half_headline" style="headline"/>
    <label text="bn_halloweenoct2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c09e57f50485d106a34b518f8f5c0545"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202107" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202106_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJul2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="level_up_ascend_booster" prio="1" countdown ="1" category = "deals" >
  <config>
    <event id="deal_levelUp-booster"/>
  </config>
  <assignments>
    <background assetID="levelup_booster_s_201806.jpg"/>
    <label text="bn_levelUpBoosters_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_levelUpBoosters_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=53b5ec1d83d5a71baad4a1cab6e6d2ed"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202401" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202401_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJan2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_202411" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202402.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocFeb2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202507" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202507_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJul2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="shipUpgradeModules" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="ship_modules_upgrade_s_201908.jpg"/>
    <label text="bn_shipUpgradeModules_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_shipUpgradeModules_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="battlePass_halloween" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass-halloween_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c0b20e1cf16fc3fb6b3e296599dc130a"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blackFridayDiscount" prio="1" countdown ="1" category = "sales" >
  <config>
  </config>
  <assignments>
    <background assetID="sale_halloween_voucher_201810.jpg"/>
    <label text="bn_blackFridayDiscount_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blackFridayDiscount_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="alienTechAll" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="alien_tech_3pack_s_201807.jpg"/>
    <label text="bn_alienTechAll_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_alienTechAll_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=08697dfc1cc6f7149869bb414452e0f9"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="novasales" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202212_CaptainSystem.jpg"/>
    <label text="bn_novasales_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_novasales_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=0dbddd8e19c47ae7c412a0a1b179a69b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battlePass_winter" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass-winter_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a4882d1480c29682a6ce8a913520d5f3"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="shipPlusNov2022" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_shipupgradenov2022.jpg"/>
    <label text="bn_shipupgradenov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_shipupgradenov2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fdb368ce3b0f89c9752d17219f3759bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianMar2023" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_2303.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianMarch2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202204" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202204_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbApr2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="goalrush2025" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_goalrush_Jun2025.jpg"/>
    <label text="bn_goalrush_2024_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_goalrush_2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1de2558ec1134d5dfafceb9adfd7dcf7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="halloweenoct2021" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_halloweenoct2021.jpg.png"/>
    <label text="bn_halloweenoct2020_headline" position="half_headline" style="headline"/>
    <label text="bn_halloweenoct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="battle_for_influence_VRU" prio="1" countdown ="1" category = "events">
  <config>
  </config>
  <assignments>
    <background assetID="faction_vru_s_201802.jpg"/>
    <label text="bn_battleforinfluenceVRU_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battleforinfluenceVRU_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="empyrian_202603" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202603.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Mar2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="shipPlusFeb2023" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Ship_Plus_Batch_6.jpg"/>
    <label text="bn_shipupgradenov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_shipupgradefeb2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fdb368ce3b0f89c9752d17219f3759bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unstableRerollDiscount" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_unstableExpansion2021.jpg"/>
    <label text="bn_unstableRerollDiscount_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unstableRerollDiscount_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="obsidian202406" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202406.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianJune2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202601" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202601.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Jan2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202501" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202501.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Jan2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="subscriptions" prio="1" countdown ="1" category = "deals" >
  <config>
    <event id="deal_best-subscription"/>
  </config>
  <assignments>
    <background assetID="best-subscriptions_s_201803.jpg"/>
    <label text="bn_subscriptions_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_subscriptions_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=43851d70ecd272bd7b584a4864063fcf"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_202502" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202502.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocFeb2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_202511" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202511.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocNovember2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202608" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202608.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Aug2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battlePass" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="specialWeekend102020" prio="1" countdown ="1" category = "events" >
  <config>
    <event id=""/>
  </config>
  <assignments>
    <background assetID="breaking_news_specialweekend102020.jpg"/>
    <label text="bn_specialweekend102020_headline" position="half_headline" style="headline"/>
    <label text="bn_specialweekend102020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_ggAction_button"  position="center">
      <onclick>
        <link href="?action=internalGalaxyGates"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202304" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202304_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbApr2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chinesenewyear202501" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_prosperousJan2025.jpg"/>
    <label text="bn_prosperous2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_prosperous2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=749409e31e062c48a55711c568c1008e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="ee_and_jv_sale" prio="1" countdown ="1" category = "deals" >
  <config>
    </config>
  <assignments>
    <background assetID="ee-jv_s_201802.jpg"/>
    <label text="bn_eejvsale_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_eejvsale_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_2026047" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202604_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbApr2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="goalrush2024england" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_goalrush_england.jpg"/>
    <label text="bn_goalrush_2024_1_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_goalrush_2024_1_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1de2558ec1134d5dfafceb9adfd7dcf7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="halloweenoct2021_test" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_halloweenoct2021.jpg.png"/>
    <label text="bn_halloweenoct2020_headline" position="half_headline" style="headline"/>
    <label text="bn_halloweenoct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blitz400_tspenderOli" prio="1" countdown ="1" category = "news" >
  <config>
  <event id="TsIndoctrineOilHappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_ts-400_b_201803.jpg"/>
    <label text="be_blitz400tsLast_content" position="half_headline_inline" style="footer_small"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3c3e53d7777c3570e81887c5e7711675"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="alienTechSaimon" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="alien_tech_saimon_s_201807.jpg"/>
    <label text="bn_alienTechSaimon_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_alienTechSaimon_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a6196b3042abe1bcdeb3483366fac2d8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202404" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202404_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbApr2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apocalypse_bk_news" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_201902.jpg"/>
    <label text="bn_apocReshuffle_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocReshuffle_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="Voyagers2607" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Voyagers__Ascent_202607_303x168.jpg"/>
    <label text="bn_voyagers-ascen_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_voyagers-ascen_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d9f23a01b5fbaddc8331a712478e8a81"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="test_news" prio="1" countdown ="0" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="trPriceSpecial2018.jpg"/>
    <label text="bn_trPriceSpecial2018_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_trPriceSpecial2018_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="footer">
      <onclick>
        <payment category="101" package=""/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="contentexpansion202106" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_contentexpansion_202106.jpg"/>
    <label text="bn_contentexpansion202106_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_contentexpansion202106_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="apoc_refresh_202405" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202405.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocMay2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianMar2020" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202003.jpg"/>
    <label text="bn_obsidianSep2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianMar2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_202605" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202605.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocMay2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="summermini2025" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ChaosOmen2024.jpg"/>
    <label text="bn_summerminievent2024_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_summerminievent2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a9af4f280836bcd7f310f4373141edfd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202601" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202601_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJan2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="shipPlusMay2022" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_shipupgrademay2022.jpg"/>
    <label text="bn_shipupgradenov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_shipupgrademay2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fdb368ce3b0f89c9752d17219f3759bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galaxy_gate_special_reward" prio="1" countdown ="1" category = "events" >
  <config>
    <event id=""/>
  </config>
  <assignments>
    <background assetID="gg_weekend_s_201802.jpg"/>
    <label text="bn_ggWeekend_headline" position="half_headline" style="headline"/>
    <label text="bn_ggWeekend_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_ggAction_button"  position="center">
      <onclick>
        <link href="?action=internalGalaxyGates"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="goalrush2024" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_goalrush_Jun2024.jpg"/>
    <label text="bn_goalrush_2024_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_goalrush_2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1de2558ec1134d5dfafceb9adfd7dcf7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianDec2022" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202212.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianDec2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidian202412" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202412.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianDecember2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="honorWeek" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="honor_25_b_201903.jpg"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="obsidian202509" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202509.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianSep2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="hitacAssault_202608" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_hitacAssault_202508.jpg"/>
    <label text="bn_hitacAssault_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_hitacassault202508_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7503b7d45fd337deee4ec5d8a0bc4dbd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_202402" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202402.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocFeb2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apocalypse_refresh_Jun2019" prio="1" countdown ="1" category = "deals" >
  <config>
   </config>
  <assignments>
    <background assetID="bbox_apoc_s_201906.jpg"/>
    <label text="bn_apocJun2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocJun2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="bk_and_lf_sale" prio="1" countdown ="1" category = "deals">
  <config>
    <event id="dealOffer"/>
  </config>
  <assignments>
    <background assetID="bootykey-logfile_s_201802.jpg"/>
    <label text="bn_bklfsale_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_bkjfsale_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidian_202403" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202403.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianMarch2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_201910" prio="1" countdown ="1" category = "deals" >
  <config>
    </config>
  <assignments>
    <background assetID="bbox_rb_s_201909.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbOct2018_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="shipPlusNov2021_wButton" prio="1" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_upgradeship2021.jpg"/>
    <label text="bn_shipupgradenov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_shipupgradenov2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="bonus_gg_reward" prio="1" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_bonusgg.jpg"/>
    <label text="bn_bonusRewards_headline" position="half_headline" style="headline"/>
    <label text="bn_bonusRewards_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_ggAction_button"  position="center">
      <onclick>
        <link href="?action=internalGalaxyGates"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battlePass_valentine" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass-valentine_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7083b7b8983d41896e7acac7bb41ddd4"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_aug2023" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202308.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocAug2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidian_bk_news" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_201903.jpg"/>
    <label text="bn_obsidianReshuffle_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianReshuffle_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidian202609" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202609.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianSep2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="goalrush20244" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_goalrush_4.jpg"/>
    <label text="bn_goalrush_2024_1_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_goalrush_2024_1_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1de2558ec1134d5dfafceb9adfd7dcf7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_Nov2019" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_201911.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocNov2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="amazonPrimeDe" prio="1" countdown ="0" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="amazon_prime_de_b_201806.jpg"/>
  </assignments>
  <actions>
    <button style="invisible_full_size_overlay"  text="bn_empty"  position="full_size">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=0ff9a2c205a58869a0a12b6bdd62ce21"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="summermini2024" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ChaosOmen2024.jpg"/>
    <label text="bn_summerminievent2024_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_summerminievent2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=734674d63d241709815dba2e03a2ba5f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battlePass_eternalGate" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass-eternalGate_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3176b6d1880bccbece4bac4d64d80d07"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="alienTechSibelonit" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="alien_tech_sibelonit_s_201807.jpg"/>
    <label text="bn_alienTechSibelonit_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_alienTechSibelonit_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c4f563bd821c48abdd2393d4a0351972"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_nov2022" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202211.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocNov2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="FiestaGate2026" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_FiestaGate_202512.jpg"/>
    <label text="bn_fiestagate2025_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_fiestagate2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c3463c5015c598423d8d757dbd29cf70"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="captainmay23_withSpecialPacks" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_captainmay23.jpg"/>
    <label text="bn_captainmay23_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_captainmay23_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fb55358a903e27d1bb0a89102b657b56"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202406" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_Jun2024.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Jun2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78584571995bb1538ddec7e1516cf816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="thanksgivingnov2020" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_thanksgivingnov2020.jpg"/>
    <label text="bn_thanksgivingnov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_thanksgivingnov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="plutus_experiments" prio="1" countdown ="1" category = "events" >
  <config>
    <event id="NpcSpawningBeacon"/>
  </config>
  <assignments>
    <background assetID="plutus_experiment_2019_compressed.jpg"/>
    <label text="bn_npcSpawningBeacon_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_npcSpawningBeacon_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="SeasonPass" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Season_Pass_Mar_2023_b.jpg"/>
    <label text="bn_SeasonPass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=57019f5104491c79b8dd52e521475c11"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianMar2021" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202103_breakingnews.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianMar2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="vog_202508" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_vog_202508.jpg"/>
    <label text="bn_strikeandexit_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_strikeandexit_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=45061033e9199d25e54f9d0416dbba20"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="perseusGrace202509" prio="1" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_PerseusGrace_202509.jpg"/>
    <label text="bn_perseusgrace2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_perseusgrace2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=180b20f6b31f57611a0d449f54664d6d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_Aug2019" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_201908.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocAug2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chinesenewyearjan2023" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_prosperous_2023.jpg"/>
    <label text="bn_prosperous2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_prosperous2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=749409e31e062c48a55711c568c1008e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="goalrush20242" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_goalrush_2.jpg"/>
    <label text="bn_goalrush_2024_1_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_goalrush_2024_1_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1de2558ec1134d5dfafceb9adfd7dcf7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202407" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202407_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJul2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidian202403" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202309_breakingnews_new.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianSep2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202207" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202207_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJul2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="Honor_Day" prio="1" countdown ="1" category = "events" >
  <config>
    <event id="50percentHonorEvent"/>
  </config>
  <assignments>
    <background assetID="honor-day_s_201802.jpg"/>
    <label text="bn_honorday_headline" position="half_headline" style="headline"/>
    <label text="bn_honorday_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalPayment"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="perseusGrace202309" prio="1" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_PerseusGrace_Sep2023_fix.jpg"/>
    <label text="bn_perseusgrace2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_perseusgrace2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=9c98d7b139421448f17d68d5d1a1574b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianSep2021" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202109_breakingnews.jpg"/>
    <label text="bn_obsidianSep2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianSep2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidian202506" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202506.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianJune2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="apoc_refresh_202608" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_202608.jpg"/>
    <label text="bn_apocAug2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocMay2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202101" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_r_b_s_202012_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbJan2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="rnb_rework_202604" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_rb_s_202604_breakingnews.jpg"/>
    <label text="bn_rbJul2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbApr2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="hitacAssault_202408" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_hitacAssault_202408.jpg"/>
    <label text="bn_hitacAssault_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_hitacassault202408_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7503b7d45fd337deee4ec5d8a0bc4dbd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="empyrian_202403" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_empyrian_202403.jpg"/>
    <label text="bn_empyrianMarch2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_empyrian_Mar2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2aeff0b8335da034af76f9d1d1e9d89f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="battlePass_protegitPandemonium" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="bn_battlePass_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_battlePass-chaos_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=458dbb88cc7d255802ea466dc18b9db2"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="obsidianSep2023" prio="1" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_202309_breakingnews_new.jpg"/>
    <label text="bn_obsidianDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_obsidianSep2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="TrinityTrials2601" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_trinityTrialsJan2026.jpg"/>
    <label text="bn_trinitytrials_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_trinitytrials_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5b3ca5a8c630432658765d32e3d7219b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="TrinityTrials2605" prio="1" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_trinityTrialsJan2026.jpg"/>
    <label text="bn_trinitytrials_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_trinitytrials_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=8afcc4eeb736332e68b40910b11ec844"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendar202503" prio="1" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_miniclientcalendar202503.jpg"/>
    <label text="bn_clientcalendar_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendar-8d_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="AsmodeusLaser2023" prio="2" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_asmodeusLaser_202308.jpg"/>
    <label text="bn_AsmodeusLaser_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_AsmodeusLaser_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=8b2f5e47d221a02a5a70e633186fd5e5"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2Jul2023" prio="2" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking2jul2023.jpg"/>
    <label text="bn_blacklightranking2apr2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2-jul2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="GG_SpecialWeekend" prio="2" countdown ="1" category = "events" >
  <config>
    <event id="GGWeekEnd_Delta_AwesomeDrones"/>
    <event id="GGWeekEnd_Delta_CJ_ChimeraPhantom"/>
    <event id="GGWeekEnd_Delta_GoliathSurprise"/>
    <event id="GGWeekEnd_Delta_LF4"/>
    <event id="GGWeekEnd_Epsilon_AwesomeDrones"/>
    <event id="GGWeekEnd_Epsilon_CJ_ChimeraPhantom"/>
    <event id="GGWeekEnd_Epsilon_CJ_MirageEnigma"/>
    <event id="GGWeekEnd_Epsilon_GoliathSurprise"/>
    <event id="GGWeekEnd_Lambda_CJ_ChimeraPhantom"/>
    <event id="GGWeekEnd_Lambda_CJ_MirageEnigma"/>
    <event id="GGWeekEnd_Streuner_AwesomeDrones"/>
    <event id="GGWeekEnd_Streuner_CJ_ChimeraPhantom"/>
    <event id="GGWeekEnd_Streuner_GoliathSurprise"/>
    <event id="GGWeekEnd_Streuner_LF4"/>
  </config>
  <assignments>
    <background assetID="sale_galaxy_gate_b_201805.jpg"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_ggAction_button"  position="higher_button">
      <onclick>
        <link href="?action=internalGalaxyGates"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galaxytrek202510" prio="2" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_galaxytrek20251015.jpg"/>
    <label text="bn_SpaceSearch202509_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SpaceSearch202509_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=83a23b9d173ed82885a1f357393e4e28"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="LevelupResourceSales_202509" prio="2" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_LevelupResourceSales202509.jpg"/>
    <label text="bn_levelupResourceSaleSep2025_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_levelupResourceSaleSep2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=49822921f5f8c1ae259f0df9459b1311"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="ArmoryUnlock2512" prio="2" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ParticleCannonRelease202512.jpg"/>
    <label text="bn_ParticleCannonRelease_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_ParticleCannonRelease_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e02099ce9bf593fdde5525b5ce82c177"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking1Jul2023" prio="2" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1jul2023.jpg"/>
    <label text="bn_blacklightranking1apr2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1-jul2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="galaxytrek202509" prio="2" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_galaxytrek202510.jpg"/>
    <label text="bn_SpaceSearch202509_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SpaceSearch202509_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=83a23b9d173ed82885a1f357393e4e28"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="PoP_202308" prio="2" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_PoP_202308.jpg"/>
    <label text="bn_titlefrenzy202308_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_titlefrenzy202308_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=88d059dbef3941209c4a8c9e6b3678b4"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="OdysseusLaser2024" prio="2" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_asmodeusLaser_202403.jpg"/>
    <label text="bn_OdysseusLaser_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_OdysseusLaser_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=711febbcb6f5c9c64a59fec0e031f816"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="GG_SpecialWeekend_NOVA" prio="2" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GG_SpecialWeekend_NOVA_1.jpg"/>
    <label text="bn_ggWeekend_content" position="half_maintext_with_headline" style="default"/>
    <label text="bn_ggWeekend_headline" position="half_headline" style="bold_full_content"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_ggAction_button"  position="higher_button">
      <onclick>
        <link href="?action=internalGalaxyGates"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsAug2023_1" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-aug2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="InternalACPTestBN" prio="3" countdown ="1" category = "events" categoryOverrideKey="bn_category_events" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_201803.jpg"/>
    <overlay assetID="banner_percentage_62.png"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="alienEggsEaster2023" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202304_Easter.jpg"/>
    <label text="bn_easter2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_easter2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=53150694c737cf92f0dbb686d7155ef4"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="pirate_raid" prio="3" countdown ="1" category = "events">
  <config>
  </config>
  <assignments>
    <background assetID="pirate-raid_s_201802.jpg"/>
    <label text="bn_pirateRaid_headline" position="half_headline" style="headline"/>
    <label text="bn_pirateRaid_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="chrominrushfeb2023" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chrominRushFeb2023.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushfeb2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushjul2021" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_breakingnews_chrominRush.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominRush_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202408" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_202408.jpg"/>
    <label text="bn_SeasonPass202408_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202408_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=71d04a63ea2eb4f92386a8c468d6279c"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking1nov2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1nov2020_new.jpg"/>
    <label text="bn_blacklightranking1nov2020_headline" position="half_headline" style="headline"/>
    <label text="bn_blacklightranking1nov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1bdde97e1095254b94e08d2a65068e7c"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="PreBlackFridayNov2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_pre_blackfridaysales2022_new.jpg"/>
    <label text="bn_pre-blackfridaysales2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_pre-blackfridaysales2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=ef951473244329bf58fa0b5ed684b412"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="epionDesignSale2022_noGGdrop" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_epionDesignSale2022.jpg"/>
    <label text="bn_epionDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_epionDesignSale2022-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f5f665e3da86f85c7563372acd569ca3"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202508" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_202511.jpg"/>
    <label text="bn_SeasonPass202511_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202511_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d056022c656b17f147d2c78779cc7b1b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="protegitPandemonium202605" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ProtegitPandemonium_May2026.jpg"/>
    <label text="bn_protegitPandemonium202305_headline" position="half_headline" style="headline"/>
    <label text="bn_protegitPandemonium202305_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=47d6142ce01dc6fc413f03e4c89fac9e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="protegitPandemonium2023" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="chaos_protegit_s_202001.jpg"/>
    <label text="bn_chaosProtegit_headline" position="half_headline" style="headline"/>
    <label text="bn_chaos202205_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="alienEggsEaster2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_breakingnews_easterSales2020.jpg"/>
    <label text="bn_alienEggsEaster_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_alienEggsEaster_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=6da91dced8c5ccac5f60946d18c1a490"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsAug2023_2" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-aug2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="alienEggsEaster2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_EasterApr2022_1.jpg"/>
    <label text="bn_alienEggsEaster2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_alienEggsEaster2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=22393b57ca903afab6742e0a15cd74a6"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202502" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_202502.jpg"/>
    <label text="bn_SeasonPass202502_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202502_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f2ab434bf69049d2251dc3e6d1d17084"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202307" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_Jun2023_1.jpg"/>
    <label text="bn_SeasonPass202311_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202311_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cb32a846106f0bb7a47a7da8c20879b8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="DSE202505" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_DSE_202505.jpg"/>
    <label text="bn_expeditionlaunch_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_expeditionlaunch_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=b4453ffb5192b7059b27bbc8029e051a"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushnov2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chromin_rush_2022_nov.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushnov2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="spectrumDesignOct2020_noGGdrop" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_spectrumDesigns2020.png"/>
    <label text="bn_spectrumDesignOct2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_spectrumDesignOct2020-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c0cf0b071bc4c61f7333666d973eb0cd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="preblacklightsalenov2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_preblacklightsalenov2020.png"/>
    <label text="bn_preblacklightsalenov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_preblacklightsalenov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d906920cc88042a63aac2d3c2725485a"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2nov2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking2jan2021.jpg"/>
    <label text="bn_blacklightranking2nov2020_headline" position="half_headline" style="headline"/>
    <label text="bn_blacklightranking2nov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5137b7f675e6ea6dca25a5abb1724544"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="epionDesignSale2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_epionDesignSale2022.jpg"/>
    <label text="bn_epionDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_epionDesignSale2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f5f665e3da86f85c7563372acd569ca3"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chaos202105" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chaos202105.jpg"/>
    <label text="bn_chaosProtegit_headline" position="half_headline" style="headline"/>
    <label text="bn_chaos202105_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="SeasonPass202505" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_202505.jpg"/>
    <label text="bn_SeasonPass202505_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202505_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f2ab434bf69049d2251dc3e6d1d17084"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202405" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_May2024_1.jpg"/>
    <label text="bn_SeasonPass202405_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202405_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cb32a846106f0bb7a47a7da8c20879b8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="protegitPandemonium202505" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ProtegitPandemonium_May2025.jpg"/>
    <label text="bn_protegitPandemonium202305_headline" position="half_headline" style="headline"/>
    <label text="bn_protegitPandemonium202305_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=64f3968394b8fe362db19098d9d1ef70"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsAug2024_2" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-aug2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202602" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_202602.jpg"/>
    <label text="bn_SeasonPass202602_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202602_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d056022c656b17f147d2c78779cc7b1b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="vortex_of_terror" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="vortex-of-terror_s_201802.jpg"/>
    <label text="bn_terror_headline" position="half_headline" style="headline"/>
    <label text="bn_terror_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="chrominrushmar2023" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chrominRushMar2023.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushmar2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="curcubitor_2019" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="curcubitor_rework_s_201910.jpg"/>
    <label text="bn_curcubitorRework_headline" position="half_headline" style="headline"/>
    <label text="bn_curcubitorRework_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="alienEggsEaster2025" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202504_Easter.jpg"/>
    <label text="bn_easter2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_easter2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=53150694c737cf92f0dbb686d7155ef4"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushaug2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chromin_rush_2022_aug.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushaug2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrush202401" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chromin_rush_2024_jan.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominRush_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominRush" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chrominrush_202107.jpg"/>
    <label text="bn_chrominrushjul2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushjul2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushdec2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chromin_rush_2022_dec.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushdec2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="spectrumDesignOct2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_spectrumDesigns2020.png"/>
    <label text="bn_spectrumDesignOct2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_spectrumDesignOct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c0cf0b071bc4c61f7333666d973eb0cd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="alienEggsEaster2026" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202604_Easter.jpg"/>
    <label text="bn_easter2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_easter2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=53150694c737cf92f0dbb686d7155ef4"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushjul2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chromin_rush_2022_jul.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushjul2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="tyrannosDesignSale2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_springsalesMar2022.jpg"/>
    <label text="bn_tyrannosDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_tyrannosDesignSale2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=246ae42de5655371dbc2dc370e443baf"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="domination" prio="3" countdown ="1" category = "events">
  <config>
    <event id="DominationEvent"/>
  </config>
  <assignments>
    <background assetID="domination_s_201802.jpg"/>
    <label text="bn_domination_headline" position="half_headline" style="headline"/>
    <label text="bn_domination_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="sentinelDesignsNov2020_noGGdrop" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_sentinelDesigns2020.jpg"/>
    <label text="bn_sentinelDesignNov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_sentinelDesignNov2020-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f16ff0413098518998ae94bb63fc15a8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="yurisday" prio="3" countdown ="1" category = "events">
  <config>
  </config>
  <assignments>
    <background assetID="yuris-day_s_201802.jpg"/>
    <label text="bn_yuris_headline" position="half_headline" style="headline"/>
    <label text="bn_yuris_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightnov2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightnov2020_new.jpg"/>
    <label text="bn_blacklightnov2020_headline" position="half_headline" style="headline"/>
    <label text="bn_blacklightnov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=356b558c46e9a7180341c4906401b32c"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushnov2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chrominrushnov2020.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominRush_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chaos202205" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ProtegitPandemonium2022.jpg"/>
    <label text="bn_chaosProtegit_headline" position="half_headline" style="headline"/>
    <label text="bn_chaos202205_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1d8961b153f55cc5ae711e966edcd1dc"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="halloweenoct2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_halloweenoct2020.jpg"/>
    <label text="bn_halloweenoct2020_headline" position="half_headline" style="headline"/>
    <label text="bn_halloweenoct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightSurge" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_breakingnews_blsurge.jpg"/>
    <label text="bn_blacklightSurge_headline" position="half_headline" style="headline"/>
    <label text="bn_blacklightSurge_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1122b334a9e30b5e0752056cc94423ca"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="protegitPandemonium202305" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ProtegitPandemonium_May2023.jpg"/>
    <label text="bn_protegitPandemonium202305_headline" position="half_headline" style="headline"/>
    <label text="bn_protegitPandemonium202305_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=ef1ec2250139c24ee5ccf11f1d7f0085"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="carboniteDesignsSep2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_carboniteDesignsSep2020.jpg"/>
    <label text="bn_carboniteDesignsSep2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_carboniteDesignsSep2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7b5f93f44d704019c65b0d6753b962e6"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202311" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_Nov2023.jpg"/>
    <label text="bn_SeasonPass202311_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202311_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cb32a846106f0bb7a47a7da8c20879b8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202402" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_Feb2024.jpg"/>
    <label text="bn_SeasonPass202402_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202402_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cb32a846106f0bb7a47a7da8c20879b8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrush202403" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chromin_rush_2024_mar.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominRush_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="tyrannosDesignSale" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_TyrannosDesignSale.png"/>
    <label text="bn_tyrannosDesignSale_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_tyrannosDesignSale_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=9d1053f0a37323ca10b486a094b3738d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202605" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_202605.jpg"/>
    <label text="bn_SeasonPass202605_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202605_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d056022c656b17f147d2c78779cc7b1b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202511" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_202511.jpg"/>
    <label text="bn_SeasonPass202511_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202511_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d056022c656b17f147d2c78779cc7b1b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="BlackFridayRally2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Rally_Sales_Nov_2022.jpg"/>
    <label text="bn_RallySalesNov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_RallySalesNov2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a13806e7e450f9c6cc241eb078480fac"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsAug2024_1" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-aug2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushjan2023" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chrominRushJan2023.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushjan2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushoct2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chromin_rush_2022_oct.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushoct2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="protegitPandemonium" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="chaos_protegit_s_202001.jpg"/>
    <label text="bn_chaosProtegit_headline" position="half_headline" style="headline"/>
    <label text="bn_chaosProtegit_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="protegitPandemonium202405" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ProtegitPandemonium_May2024.jpg"/>
    <label text="bn_protegitPandemonium202305_headline" position="half_headline" style="headline"/>
    <label text="bn_protegitPandemonium202305_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f6a7202ae5863444f057deaf6b8686d4"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="Athena2024" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Olympic202407.jpg"/>
    <label text="bn_olympic2024_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_olympic2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2df3c4583fe8ca5ab2e40005b40cf40f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202411" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_202411.jpg"/>
    <label text="bn_SeasonPass202411_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202411_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f2ab434bf69049d2251dc3e6d1d17084"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushsep2022" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chromin_rush_2022_sept.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominrushsep2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="alienEggsEaster2024" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202403_Easter.jpg"/>
    <label text="bn_easter2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_easter2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=53150694c737cf92f0dbb686d7155ef4"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass202608" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="news_Season_Pass_202608.jpg"/>
    <label text="bn_SeasonPass202508_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202608_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d056022c656b17f147d2c78779cc7b1b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="SeasonPass2024051" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SeasonPass_May2024_1.jpg"/>
    <label text="bn_SeasonPass202405_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_SeasonPass202405_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
      </onclick>
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cb32a846106f0bb7a47a7da8c20879b8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking3nov2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking3jan2021.jpg"/>
    <label text="bn_blacklightranking3nov2020_headline" position="half_headline" style="headline"/>
    <label text="bn_blacklightranking3nov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=19c04ee148e6d633585d045647c61a3d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominrushjan2024" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_chromin_rush_2024_jan.jpg"/>
    <label text="bn_chrominRush_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominRush_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="sentinelDesignsNov2020" prio="3" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_sentinelDesigns2020.jpg"/>
    <label text="bn_sentinelDesignNov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_sentinelDesignNov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f16ff0413098518998ae94bb63fc15a8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AAUpdate202304" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AstralAscensionExpansion.jpg"/>
    <label text="bn_AAUpdate202304_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_AAUpdate202304_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="spearheadDesigns2019" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="designdeal_spearhead_q3_s_201908.jpg"/>
    <label text="bn_spearheadDesigns2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_spearheadDesigns2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c9ecc35420ded6dc131ae72aa7da1967"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsAug2022_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralranking2aug2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3b4579d21d14a5531bebca4f69ca4115"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="indoctrinesaledec2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_BE_indoctrinesaledec2021.jpg"/>
    <label text="bn_indoctrinesaledec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_indoctrinesaledec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=8af4f4742a07b0d4e6d0fd09bde22092"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="stellar_pathfinder_noVanguard" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="stellar_pathfinder_b_201907.jpg"/>
    <label text="bn_stellarPathfinder_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c29642305bfcb587dea1e08b86f4bf36"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202609" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202609.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202609_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202601" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202601.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202601_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AgatusBreach202504" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202504.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202504_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="gauntletOfPlutus202507" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gauntletOfPlutusJuly2025.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutusJul2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c3b347f475ec9f9b56e104ef7f6a40a5"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="carboniteDesigns2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_carboniteDesign.jpg"/>
    <label text="bn_carboniteDesigns2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_carboniteDesigns2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7de495d735632ab5b780a45d4f0d5e22"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="autumnDesignSep2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AutumnDesignSep2024.jpg"/>
    <label text="bn_autumnDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_autumnDesignSep2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=733a1b5175660a80ef1de054c5fd4fd5"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="basilisk202309" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_basilisk202309.jpg"/>
    <label text="bn_basilisk202309_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_basilisk202309_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5ec6be8848d8f270a28f45ecd6c34879"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="frozenLabyrinth" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="winterevent_start_s_201912.jpg"/>
    <label text="bn_frozenLabyrinth_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_frozenLabyrinth_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="eternalGate" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="eternal_gate_s_202004.jpg"/>
    <label text="bn_eternalGate_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_eternalGate_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="berserkerDesignAug2021_noGGdrop" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_shipDesignAug2021.jpg"/>
    <label text="bn_berserkerDesignAug2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_berserkerDesignAug2021-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5013d9d59e9eba4d285342a66225c50e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange202403" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchantExchange2022.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5a929e4b33d68ca98db2b61d0f27d722"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsOct2022_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1jun2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-oct2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d0f2fbaea2e8d3cc493511fb0cbcb865"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="stellar_pathfinder" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="stellar_pathfinder_b_201907.jpg"/>
    <label text="bn_stellarPathfinder_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5bc744f56db057217d7f94d2f1e01bd3"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AARecipeRefresh202301" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AstralAscensionExpansion.jpg"/>
    <label text="bn_AARecipeRefresh202301_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_AARecipeRefresh202301_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="monthlyRankingUpdate_Jan2023" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_monthlyRankingJan2023.jpg"/>
    <label text="bn_monthlyRankingUpdateJan2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_monthlyRankingUpdateJan2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="infernoPetDesigns2020_noGGdrop" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_petDesignSalesSep2020.jpg"/>
    <label text="bn_infernotPetDesigns2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_infernotPetDesigns2020-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fcf2fa2822082b7364429e96f86885fc"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="contentexpansion_202106_sales" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_contentexpansion_202106_sales.jpg"/>
    <label text="bn_retrieversales2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_retrieversales2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankings202512_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-dec2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientbonusoct2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_clientbonusoct2020.jpg"/>
    <label text="bn_clientbonusoct2020 _headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientbonusoct2020 _content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="worldBoss202406" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_worldboss_Jun2024.jpg"/>
    <label text="bn_worldBoss202306_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_worldBoss202306_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5ee9ac47ecb84bc396439723dd558346"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsJun2025_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-jun2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="indoctrinesaledec2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_BE_indoctrinesaledec2021.jpg"/>
    <label text="bn_indoctrinesaledec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_indoctrinesaledec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=148d12912e27e3e6392b9b759358dc70"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="uriBank_bonusBooster" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="uriBank_bonusBooster.jpg"/>
    <label text="bn_uridiumBank_bonus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_uriBank_bonusBooster_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="VIPMerchantExchange202609" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchant202504.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=78960c071d831be95749788a3701d7eb"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_202509" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_Sep2025.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=bfc32fd2aea1c01c7299388b5f0ceee9"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterquest2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_winterquests2020.jpg"/>
    <label text="bn_winterQuests2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterQuests_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="GGWeekend_GChampion" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GGWeekendGChampion.png"/>
    <label text="bn_GGWeekend_GChampionDesigns_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_GGWeekend_GChampionDesigns_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="retentionQuestsJul2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_summerQuests.jpg"/>
    <label text="bn_retentionQuestsJul2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_retentionQuestsJul2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="12th_birthday" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="birthday_12_b_201812.jpg"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking2Jan2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_2sep2022.jpg"/>
    <label text="bn_blacklightranking2nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2-jan2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankingsJun2024_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-jun2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="petEquipmentSales" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_petExpansion.jpg"/>
    <label text="bn_petEquipmentSales_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_petEquipmentSales_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a6b5b29ef4ee6e213fcc602259c5e9cd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="hitacAssault" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="hitac_assault_s_201804.jpg"/>
    <label text="bn_hitacAssault_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_hitacAssault_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d2778f0511b127944cdf25eeb639ad78"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="miniclientReward" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_miniclientReward.jpg"/>
    <label text="bn_miniclientReward_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_miniclientReward_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankings202404_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-apr2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="pveServer_rerunSales" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_pveserverfeb2021.jpg"/>
    <label text="bn_pveserver_rerunsales_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_pveserver_rerunsales_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="extraEnergyDeal" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="ee-jv_s_201802.jpg"/>
    <overlay assetID="banner_percentage_56.png"/>
    <label text="bn_extraEnergyDeal_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_extraEnergyDeal_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=13902c98bdb409b7a356900e0ab0e81a"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="returnofhero202507" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_returnofhero202507.jpg"/>
    <label text="bn_returnofhero2025_title" position="half_headline" style="bold_full_content"/>
    <label text="bn_returnofhero2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="agatussep2020" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatussep2020.jpg"/>
    <label text="bn_agatussep2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatussep2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=08d7d7eddd29805c21ca8fb70ab0bd6b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="monthlyRanking" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_monthlyRanking.jpg"/>
    <label text="bn_monthlyRankingUpdate_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_monthlyRankingUpdate_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankings202604_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-apr2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="hecateDesigns2019_noGGdrop" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_pveserverjan2021_sales.jpg"/>
    <label text="bn_hecateDesigns2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_hecateDesigns2019-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7c0e74ba069ce118bdb8966097cad0de"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterEvent" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="winterevent_calendar_s_201912.jpg"/>
    <label text="bn_winterEvent_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterEvent_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="AgatusBreach202502" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202502.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202502_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_202604" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_202604.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=bfc32fd2aea1c01c7299388b5f0ceee9"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankings202412_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-dec2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="DARKORBIT_30991_test" prio="4" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="xp_25_b_201903.jpg"/>
    <label text="" position="full_size" style="bold_full_content"/>
    <label text="" position="footer" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="valentine2026" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_valentine2026.jpg"/>
    <label text="bn_valentine_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_valentine2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=8ee4acdcbbc24c9156cadaa54fc1d6eb"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterdec2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202512_WinterEvent.jpg"/>
    <label text="bn_winterdec2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterdec2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e61c00f9b53ed948f8b90551d9ca25e2"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking1Jul2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Gauntlet_of_Plutus_2022.jpg"/>
    <label text="bn_blacklightranking1apr2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1-jul2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="gauntletofPlutusJan2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gauntletOfPlutusJan2024.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutusJan2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=28baed452c09974f4cd302ba7d36ded6"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsApr2023_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-apr2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blackfridaynov2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blackfriday_2021_02.jpg"/>
    <label text="bn_blackfridaynov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blackfridaynov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=9bcfe886a62e9761018ec8b141f4af86"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="laserStormDropsOnly" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="laserstorm_s_201804.jpg"/>
    <label text="bn_laserStormDropsOnly_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_laserStormDropsOnly_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="AgatusBreach202505" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202505.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202505_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterdec2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_wintereventdec2021_v2.jpg"/>
    <label text="bn_winterdec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterdec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2016b1af79e0c5f239975ad795cb0ee3"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="springDesignMar2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Spring202503.jpg"/>
    <label text="bn_springDesignMar2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_springDesignMar2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=13d43a2f4b20fa487e40ec7b171c1885"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterquests2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_winterquests2020.jpg"/>
    <label text="bn_winterQuests2024_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterQuests_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="galacticStrife_apr2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_galaticstrife2022.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=73d880edb86a3c08ef5a41fb21a9a148"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2feb2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking2feb2022.jpg"/>
    <label text="bn_blacklightranking2feb2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2feb2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="skollGate" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="winterevent_skoll_gate_s_201812.jpg"/>
    <label text="bn_skollGate_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_skollGate_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="pveloginbonusmar21" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_miniclientReward.jpg"/>
    <label text="bn_pveloginbonusmar2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_pveloginbonusmar2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankingsFeb2025_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-feb2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="gauntletofPlutus202407" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gauntletOfPlutusJuly2024.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutusJul2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5f5392c5deb845f000dab3f6ea58b4ed"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking1Apr2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1Apr2022.jpg"/>
    <label text="bn_blacklightranking1apr2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1apr2022_content2" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="galacticStrife_sep2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_galacticStrife_2022.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AgatusBreach202508" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202502.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202508_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="missionExpansion2018" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="mission_expansion_1_s_201807.jpg"/>
    <label text="bn_missionExpansion2018_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_missionExpansion2018_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="uriBank_bonusLevelBooster" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="uriBank_bonusLevelBooster.jpg"/>
    <label text="bn_uridiumBank_bonus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_uriBank_bonusLevelBooster_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="enhancedLF4Day" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="gg_weekend_enhanced_lf_4_s_201904.jpg"/>
    <label text="bn_eLf4Day_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_eLf4Day_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="5000dayCelebrationP2" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_5000dayCelebrationP2.png"/>
    <label text="bn_5000dayCelebrationP2_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_5000dayCelebrationP2_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="agatusBreachJan2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusoct2020.png"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="valentine2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_valentine2024.jpg"/>
    <label text="bn_valentine_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_valentine2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=21aa4af562657f08b715faf9a164eff5"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blackfridaynov2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_BlackfridayNov2024.jpg"/>
    <label text="bn_blackfridaynov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blackfridaynov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=30b0d639b75c2246415f69eb7b45dd88"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsJune2022_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1jun2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralranking1jun2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="eternalFragmentSales" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_eternalFragmentsMay2021.jpg"/>
    <label text="bn_eternalFragmentSale_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_eternalFragmentSale_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=b37f272b5d7cdf671a79e611c1d116c7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202407" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202407.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202407_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsFeb2025_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-feb2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="infernoPetDesigns2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_petDesignSalesSep2020.jpg"/>
    <label text="bn_infernotPetDesigns2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_infernotPetDesigns2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fcf2fa2822082b7364429e96f86885fc"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterquests2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_winterquests2020.jpg"/>
    <label text="bn_winterQuests2025_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterQuests_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="diminisherDesigns2020" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_diminisherDesign.jpg"/>
    <label text="bn_diminisherDesign_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_diminisherDesign_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=40e06f601442454dc9a9ae7d6c8d1095"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202308" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202308.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202308_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="frostDesignDec2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_frostDesignDec2021.jpg"/>
    <label text="bn_WinterFrost2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_WinterFrost2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fe202032df3fc17f2a7f3adcb48f2d37"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="infernoDeals2019" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="sale_designs_inferno_s_201904.jpg"/>
    <label text="bn_infernoDeals_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_infernoDeals_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d7a6859f83e478f6cb70124455b870c0"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="frostDesignDec2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_FrostDesignSales_Dec2023.jpg"/>
    <label text="bn_WinterFrost2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_WinterFrost2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=dc01f11b01d0facef0bb0c71908c37b3"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="modulesaleoct2020" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_modulesaleoct2020.jpg"/>
    <label text="bn_modulesaleoct2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_modulesaleoct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=9395eedebd47591dc374a3cca733b962"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="holoDesignSep_noGGdrop" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_holoDesignSept2021.jpg"/>
    <label text="bn_holoDesignSep2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_holoDesignSep2021-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=b0d5024df8015adcfe89e02f97252226"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mimesis2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_mimesis2021.jpg"/>
    <label text="bn_mimesisMutiny_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_mimesisMutiny_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=ab9a1f8407899527cb4dccad885809bb"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AgatusBreach202410" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202410.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202410_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="ggDrop_tartarusDesigns" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="designdeal_tartarus_q3_s_201907.jpg"/>
    <label text="bn_ggTartarusDrop_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_ggTartarusDrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="VIPMerchantExchange202509" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchant202509.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=bfce187c237c5d9d75d2084d07ba7f58"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="contentexpansion_202108_sales" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_contentexpansion_202106_sales.jpg"/>
    <label text="bn_retrieversales2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_retrieversales2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1bbfa7c18e7f721909f9a5e07a3313d8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsApr2023_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-apr2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendaroct2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_clientcalendaroct2020.jpg"/>
    <label text="bn_clientcalendaroct2020 _headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendaroct2020 _content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="agatusoct2020" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusoct2020.png"/>
    <label text="bn_agatusoct2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusoct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202408" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202408.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202408_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_sep2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_strife202109.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=73d880edb86a3c08ef5a41fb21a9a148"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="gauntletOfPlutus" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gauntlet_of_plutus_jan2021.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutus_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=32b8637c3a578be4a52ca6759daeae63"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange202407" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchantExchange202407.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7016560d3b82edb013eff7dff8534246"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="indoctrinesaledec2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_indoctrinesaledec2020.jpg"/>
    <label text="bn_indoctrinesaledec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_indoctrinesaledec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=148d12912e27e3e6392b9b759358dc70"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="autumnDesignSep2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_shipDesignAug2021.jpg"/>
    <label text="bn_autumnDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_autumnDesignSale2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5c7ac75609b000fb747c0ec3691dca88"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2Sep2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_2sep2022.jpg"/>
    <label text="bn_blacklightranking2sep2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2sep2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="galacticStrife_202609" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_202609.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=ab744b2351d2db738e4ef9c5fad8898d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="test_175_mc" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="headlin_test_175_mc" position="footer" style="headline"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="text_key_test_175_mc"  position="higher_button">
    </button>
  </actions>
</layer>

<layer name="test_2_175_mc" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="battlepass_s_201907.jpg"/>
    <label text="test_2_175_loca_mc" position="full_size" style="headline"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="text_key_test_175_mc"  position="higher_button">
    </button>
  </actions>
</layer>

<layer name="pveServer_enrichmentSales" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_202205_PVE_Sales.jpg"/>
    <label text="bn_PVE-server-enrichment-sales_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_PVE-server-enrichment-sales_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=574822c8eaa601939d4f93a0da169216"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="cyborgDeals" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="zeta_gate_event_s_201906.jpg"/>
    <label text="bn_cyborgDeals_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_cyborgDeals_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=374e5620a1e1d47e9001a21c725321ab"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendarfeb2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_miniclientcalendarjan2022.jpg"/>
    <label text="bn_clientcalendarjan2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendarfeb2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="clientcalendarjan2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_miniclientcalendarjan2022.jpg"/>
    <label text="bn_clientcalendarjan2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendarjan2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="uridiumBank" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="uridiumbank_2019.jpg"/>
    <label text="bn_uridiumBank_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_uridiumBank_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="diminisherDesigns2020_noGGdrop" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_diminisherDesign.jpg"/>
    <label text="bn_diminisherDesign_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_diminisherDesign-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=40e06f601442454dc9a9ae7d6c8d1095"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsNov2022_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralranking1aug2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3b4579d21d14a5531bebca4f69ca4115"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking3dec2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking3dec2021.jpg"/>
    <label text="bn_blacklightranking3dec2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking3dec2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking1dec2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1dec2021.jpg"/>
    <label text="bn_blacklightranking1dec2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1dec2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="VIPMerchantExchange202412" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchant202412.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f9cbd1162c4b54391dda68b84c3f5552"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202406" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202406.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202406_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsDec2023_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1jun2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-dec2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange_generic" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchantExchange2022.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5a929e4b33d68ca98db2b61d0f27d722"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchantExchange2022.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=b15f177c3e8425c8eb99266a3bce3d16"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_202504" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_202504.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=217b210be436afcd4fd1e01bbbdaaaa3"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsNov2022_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralranking2aug2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3b4579d21d14a5531bebca4f69ca4115"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_202409" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_Sep2024.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a762384840bc2635d6ef84099fb22783"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unification_special_sale" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="designdeal_cyborg_q4_s_201910.jpg"/>
    <label text="bn_unificationDesigns2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unificationDesigns2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=0aaeb985b76dab65d43229b7f672bf84"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2aug2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="blacklight_s_201810.jpg"/>
    <label text="bn_blacklightranking2aug2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2aug2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="dummyNews" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatussep2020.jpg"/>
    <label text="bn_agatussep2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatussep2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package=""/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankings202604_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-apr2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="cybermondaynov2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_cybermonday_2021.jpg"/>
    <label text="bn_cybermondaynov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_cybermondaynov2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1aa41c37996c7d14b40f674f3a342581"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsFeb2024_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-feb2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agateBreach" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agateBreach.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="returneesPackage" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Returnees_Package.jpg"/>
    <label text="bn_returnees-package_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_returnees-package_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=99402d1a2688fdeded9070d9db61728c"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202310" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202310.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202310_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="salesrerun_designs" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SalesRerun2022.jpg"/>
    <label text="bn_salesrerun_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_salesrerun_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockShipModel"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blitz400_tsRSB75spender" prio="4" countdown ="0" category = "news" >
  <config>
    <event id="TsRSB-75HappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_ts_400_v04_b_201907.jpg"/>
    <label text="" position="half_headline" style="bold_full_content"/>
    <label text="be_blitz400tsChrominRSB_content" position="half_maintext" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="footer">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=04dc5c87431b5928f3d02905e1989408"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="valentine" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="valentines_s_202002.jpg"/>
    <label text="bn_valentine_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_valentine_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="mimesis2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_mimesismutiny2025.jpg"/>
    <label text="bn_mimesisMutiny_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_mimesis2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fc2e09f472d55f43c9087c62b16bdda2"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="solaceDesigns2020" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_solaceDesigns2020.png"/>
    <label text="bn_solaceDesigns2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_solaceDesigns2020-rerun_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=b4983b11935db40c1a98b1f0a4dfc69e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsDec2022_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-dec2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d0f2fbaea2e8d3cc493511fb0cbcb865"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange_202304" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchantExchange2022.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5a929e4b33d68ca98db2b61d0f27d722"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankings202512_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-dec2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange_202309" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchant_Sep2023.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2066328d77b1fea1e50a082ca8cb2853"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="autumnDesignSep2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AutumnDesignSep2023.jpg"/>
    <label text="bn_autumnDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_autumnDesignSep2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=8e49073a9d498922539b0f837334d11a"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="5000dayCelebration" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_5000_giveaway.png"/>
    <label text="bn_5000dayCelebration_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_5000dayCelebration_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="cyborgDesignFeb2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_cyborgDesigns2021.jpg"/>
    <label text="bn_cyborgDesignFeb2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_cyborgDesignFeb2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5013d9d59e9eba4d285342a66225c50e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mercWargames" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="mwg_s_201903.jpg"/>
    <label text="bn_mercWargames_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_mercWargames_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking1feb2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1feb2022.jpg"/>
    <label text="bn_blacklightranking1feb2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1feb2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="holoDesignSep" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_holoDesignSept2021.jpg"/>
    <label text="bn_holoDesignSep2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_holoDesignSep2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=b0d5024df8015adcfe89e02f97252226"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blackfridaynov2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blackfridaynov2020.jpg"/>
    <label text="bn_blackfridaynov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blackfridaynov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=81c720108430705d6037681f7525dc56"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2Sep2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking2_sep2023.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2sep2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="agatusBreach202402" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202402.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202402_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2apr2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="blacklight_s_201810.jpg"/>
    <label text="bn_blacklightranking2apr2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2apr2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="monthlyDeluxePack102020" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_monthlyDeluxePack102020.jpg"/>
    <label text="bn_monthlyDeluxePack102020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_monthlyDeluxePack102020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsFeb2023_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralranking2-feb2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=6012ef1a8f28f87fa2c70f4566d6dc46"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="frostDesignDec2020_noGGdrop" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_frostDesignDec2020.jpg"/>
    <label text="bn_frostDesignDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_frostDesignDec2020-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=61e5431a838caf799debae4a3fdb896e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendar202501" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_clientcalendarnov2021.png"/>
    <label text="bn_newyearsales2025_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendarjan2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="agatusBreach202602" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202602.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202602_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="plagueAlert2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_breakingnews_plagueAlert2020_new.jpg"/>
    <label text="bn_plagueMutation2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_plagueMutation2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking2jun2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="blacklight_s_201810.jpg"/>
    <label text="bn_blacklightranking2jun2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2jun2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="salesrerun_extras" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SalesRerun2022.jpg"/>
    <label text="bn_salesrerun_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_salesrerun_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="gauntletofPlutusJan2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gauntletofplutusJan2023.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutusJan2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=28baed452c09974f4cd302ba7d36ded6"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightRanking2sep2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="blacklight_s_201810.jpg"/>
    <label text="bn_blacklightranking2sep2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2sep2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking3dec2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking3dec2020.png"/>
    <label text="bn_blacklightranking3dec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking3dec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="chrominRushPower_update" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_breakingnews_chrominRush.jpg"/>
    <label text="bn_chrominRushSpeed_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominRushSpeed_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsFeb2023_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralranking1-feb2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=6012ef1a8f28f87fa2c70f4566d6dc46"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsDec2022_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1jun2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-dec2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d0f2fbaea2e8d3cc493511fb0cbcb865"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202312" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202312.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202312_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AAUpdate202404" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AstralAscensionExpansion.jpg"/>
    <label text="bn_AAUpdate202304_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_AAUpdate202304_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202403" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202403.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202403_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mimesisDesigns2019" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="designdeal_mimesis_q3_s_201908.jpg"/>
    <label text="bn_mimesisDesigns2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_mimesisDesigns2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=664581aef136a0c32be13107de81517b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking1dec2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1dec2020.png"/>
    <label text="bn_blacklightranking1dec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1dec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankings202504_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-apr2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendarjan2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_miniclientcalendarjan2022.jpg"/>
    <label text="bn_clientcalendarjan2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendarjan2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankings202404_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-apr2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange202312" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchantExchange2023.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f9cbd1162c4b54391dda68b84c3f5552"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="valentine2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_valentine2023.jpg"/>
    <label text="bn_valentine_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_valentine2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=21aa4af562657f08b715faf9a164eff5"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterdec2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202412_WinterEvent.jpg"/>
    <label text="bn_winterdec2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterdec2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e61c00f9b53ed948f8b90551d9ca25e2"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralascensionJune2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_breakingnews_AstralAscension.jpg"/>
    <label text="bn_astralascension_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralascension_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d9e7f1195233ef63a7d411596114c5e5"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="summerDesignJun2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SummerDesignJun2023.jpg"/>
    <label text="bn_summerDesignJun2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_summerDesignJun2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=0f49a229cbea6846ea564b5060ee1d6c"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="hecateRelease" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="hecate_launch_compressed.jpg"/>
    <label text="bn_hecateRelease_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_hecateRelease_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fe2a0f9150279f36d36c466fc3705e69"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2Nov2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking2_Nov2023.jpg"/>
    <label text="bn_blacklightranking1nov2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2nov2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="winterdec2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202312_WinterEvent.jpg"/>
    <label text="bn_winterdec2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterdec2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=6159c3f749795520ad69b6667e601a2d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="springDesignMar2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_springdesignsales2024.jpg"/>
    <label text="bn_springDesignMar2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_springDesignMar2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cac3c49dc4998d32486692119225ca22"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unificationSaleOct2020" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_unificationsaleoct2020.jpg"/>
    <label text="bn_unificationsaleoct2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unificationsaleoct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5563a03201466e09fbf3b2db464924de"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AgatusBreach202506" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202506.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202506_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="laserStormElf4Pack" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="laserstorm_s_201804.jpg"/>
    <label text="bn_laserStormElf4Pack_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_laserStormElf4Pack_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2c38b3bfe14f1fae4dd74044da4b90fd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsDec2023_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-dec2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsJun2024_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-jun2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2Mar2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_2sep2022.jpg"/>
    <label text="bn_blacklightranking2nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2-mar2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankings202410_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-oct2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202604" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202604.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202604_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="instagram" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_instagram_breakingnews.jpg"/>
    <label text="bn_instagram_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_instagram_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_instagram_button"  position="center">
      <onclick>
        <link href="https://www.instagram.com/darkorbit/"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="newdawn202410" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_newdawn2024.jpg"/>
    <label text="bn_newdawn2024_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_newdawn2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cc19034e5b8f1743b4db3e739707f225"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="frostDesigns2019" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="designdeal_frost_q4_s_201912.jpg"/>
    <label text="bn_frostDesigns2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_frostDesigns2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cf38c6aa18a9876c07bb139f1dd3c0e9"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="springDesignMar2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_springdesignsales2023.jpg"/>
    <label text="bn_springDesignMar2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_springDesignMar2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=60773876a91e735bc2e2447f2e6740b9"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_202411" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_Nov2024.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cb3d1e116de44ac2cba03b5f997e4cf8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="summerDesignJuly2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SummerDesign202407.jpg"/>
    <label text="bn_summerDesignJun2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_summerDesignJul2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f22a69f8c8f0c05147a1ddeadef9a55e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2dec2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking2dec2021.jpg"/>
    <label text="bn_blacklightranking2dec2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2dec2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="xpWeek" prio="4" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="xp_25_b_201903.jpg"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankingsDec2024_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-dec2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="spacecupDiscount2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="deal_15percent_s_202106.jpg"/>
    <label text="bn_blackFridayDiscount2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_spacecupDiscount2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="autumnDesignSep2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AutumnDesignSep2025.jpg"/>
    <label text="bn_autumnDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_autumnDesignSep2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3f74738881491f87802dc62ee52450fa"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AgatusBreach202507" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202507.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202507_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterdec2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202212_WinterEvent.jpg"/>
    <label text="bn_winterdec2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterdec2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=6159c3f749795520ad69b6667e601a2d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsJun2023_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-jun2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202606" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202606.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202606_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="summerDesign202607" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_SummerDesign202607.jpg"/>
    <label text="bn_summerDesignJun2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_summerDesignJul2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=133d380b344156055bd05e8a32e97a95"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="valentine2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_valentine2025.jpg"/>
    <label text="bn_valentine_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_valentine2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=8ee4acdcbbc24c9156cadaa54fc1d6eb"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202404" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202404.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202404_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="frostDesignDec2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_202212_FrostDesignSales.jpg"/>
    <label text="bn_WinterFrost2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_WinterFrost2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=76faf0e37d6ecb960ac8e12777522d90"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="immortalUnion" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_small_gauntlet_of_plutus.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutus_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="spacecup202211" prio="4" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_spacecup2022.jpg"/>
    <label text="bn_spacecup202211_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_spacecup202211_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d3d6df43bce700c804f90d2c2993aa5d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="exampleBN" prio="4" countdown ="1" category = "sales" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_obsidian_s_201803.jpg"/>
    <overlay assetID="banner_percentage_62.png"/>
    <label text="bn_rbReshuffle_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbReshuffle_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package=""/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unstableShardSales" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_unstableShardSales.jpg"/>
    <label text="bn_unstableShardSales_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unstableShardSales_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fd3c1d9fc522aee0a33f150c354b290d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="chrominRushPower" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_breakingnews_chrominRush.jpg"/>
    <label text="bn_chrominRushPower_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_chrominRushPower_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e41caeef0a2d515d1ed19ccb09d24308"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="test_2" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_201803.jpg"/>
    <label text="bn_rbReshuffle_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_rbReshuffle_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="frostDesigns2019_noGGdrop" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="designdeal_frost_q4_s_201912.jpg"/>
    <label text="bn_frostDesigns2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_frostDesigns2019-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cf38c6aa18a9876c07bb139f1dd3c0e9"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mimesis202511" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_mimesismutiny202511.jpg"/>
    <label text="bn_mimesisMutiny_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_mimesis202511_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=db83a376b2683bef02d60ede3014bb51"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="worldBoss2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_worldboss_202506.jpg"/>
    <label text="bn_worldBoss202306_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_worldboss2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5f10ee0df05b8b9ac54763d0c84d892b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202411" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202411.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202411_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AgatusBreach202501" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202501.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202501_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="contentexpansion_202108" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_ce202108.jpg"/>
    <label text="bn_contentexpansion_202108_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_contentexpansion_202108_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2Nov2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_2sep2022.jpg"/>
    <label text="bn_blacklightranking2nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2nov2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="autumnDesign202509" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AutumnDesignSep2025.jpg"/>
    <label text="bn_autumnDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_autumnDesign202509_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3f74738881491f87802dc62ee52450fa"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsJune2022_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2jun2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralranking2jun2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="summesale202506" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_summersale_202506.jpg"/>
    <label text="bn_summerDealJul2025_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_summerDealJul2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=921ff329ab22e3e3afae0b4b6a8e73c2"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2apr2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="blacklight_s_201810.jpg"/>
    <label text="bn_blacklightranking2apr2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2apr2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking1sep2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1_Nov2023.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1nov2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="thanksgiving" prio="4" countdown ="1" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="thanksgiving_s_201811.jpg"/>
    <label text="bn_thanksgiving_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_thanksgiving_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="pveSale_blaze2021" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_designSale_blaze2021.jpg"/>
    <label text="bn_blaze2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blaze2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=56552b937c4815882b8df0a920301e56"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="orcusDesignMay" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_orcusDesignMay2021.jpg"/>
    <label text="bn_orcusDesignMay2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_orcusDesignMay2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=08129fb17e7fbc55d39a71efeac1e39f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="pveServer_preRegistration" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_pveserverPrelaunch2020.jpg"/>
    <label text="bn_pveServerPrelaunch_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_pveServerPrelaunch_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_pveServerPrelaunch_button"  position="center">
      <onclick>
        <link href="?action=registered"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterquests2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_winterquests2020.jpg"/>
    <label text="bn_winterQuests2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterQuests_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="clientBoxesSep2020" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_clientboxessep2020.png"/>
    <label text="bn_clientBoxesSep2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientBoxesSep2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="autumnDesignSepNoGGDrop2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AutumnShipDesignSales_Sep2022.jpg"/>
    <label text="bn_autumnDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_autumnDesignSale2022-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a7b78e086039dbcbbc93b533672842bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="alienEggsEaster" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="easter_event_s_201904.jpg"/>
    <label text="bn_alienEggsEaster_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_alienEggsEaster_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="autumnDesign202609" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AutumnDesignSep2026.jpg"/>
    <label text="bn_autumnDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_autumnDesignSep2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=17a6d1589ebfb8eb41382eeb64937a73"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blackfridaynov2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_BlackfridayNov2025.jpg"/>
    <label text="bn_blackfridaynov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blackfridaynov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=43a06bcff7b340ef52061386487ecf15"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankings202602_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-feb2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="laserStormElf4PackOnly" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="laserstorm_s_201804.jpg"/>
    <label text="bn_laserStormElf4PackOnly_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_laserStormElf4PackOnly_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=2c38b3bfe14f1fae4dd74044da4b90fd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="cyborgDesignFeb2021_noGGdrop" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_cyborgDesigns2021.jpg"/>
    <label text="bn_cyborgDesignFeb2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_cyborgDesignFeb2021-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5013d9d59e9eba4d285342a66225c50e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202307" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202307.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202307_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202311" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202311.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202311_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchantExchange2023.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1d6c2ed72d659b4be2be90c0fd5b9388"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="gauntletofPlutus202501" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gauntletOfPlutusJan2025.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutusJan2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=9781de0fcd36ef248d34fb7b224b6b11"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsAug2022_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralranking1aug2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=3b4579d21d14a5531bebca4f69ca4115"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="salesrerun" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SalesRerun2022.jpg"/>
    <label text="bn_salesrerun_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_salesrerun_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking1May2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_1sep2022.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1-may2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="spaceCup" prio="4" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="spacecup_s_201804.jpg"/>
    <label text="bn_spaceCup_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_spaceCup_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=54ada4e01522020654ca15303de033c0"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202405" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202405.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202405_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mimesis202603" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_mimesismutiny202603.jpg"/>
    <label text="bn_mimesisMutiny_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_mimesis202603_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=db83a376b2683bef02d60ede3014bb51"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="valentine2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="valentines_s_202002.jpg"/>
    <label text="bn_valentine_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_valentine_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=bf0d8b4d61010d7736b6e1172a35758f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsOct2022_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-oct2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d0f2fbaea2e8d3cc493511fb0cbcb865"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankings202602_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-feb2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_apr2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_Apr2024.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=ab965c5321e0703ba8799f311aa1d570"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="carboniteDesigns2022_noGGdrop" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_carboniteDesign.jpg"/>
    <label text="bn_carboniteDesigns2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_carboniteDesigns2022-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7de495d735632ab5b780a45d4f0d5e22"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mileageMarket_202307" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_mileagemarket.jpg"/>
    <label text="bn_MileageMarket_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_MileageMarket_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=150cfe076068a90d46c89b0b20216aed"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="GalacticStrife_nov2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_Nov2023.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=ab965c5321e0703ba8799f311aa1d570"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="hecateDesigns2019" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_pveserverjan2021_sales.jpg"/>
    <label text="bn_hecateDesigns2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_hecateDesigns2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7c0e74ba069ce118bdb8966097cad0de"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking1Sep2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1_sep2023.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1sep2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="VIPMerchantExchange2023Dec" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchantExchange2023.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=96d5e46f6fc7b2f6b2be983269decd7e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendarnov2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_clientcalendarnov2020.jpg"/>
    <label text="bn_clientcalendarnov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendarnov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="techsaleoct2020" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_techsaleoct2020.jpg"/>
    <label text="bn_techsaleoct2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_techsaleoct2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=0424c0850aa92f28a7e545acfdca5c23"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendarnov2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_clientcalendarnov2021.png"/>
    <label text="bn_clientcalendarnov2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendarnov2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="agatusBreach202605" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202605.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202605_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="monthlyRankingUpdateJan2022" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_monthly_update_jan2022.jpg"/>
    <label text="bn_monthlyRankingUpdateJan2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_monthlyRankingUpdateJan2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="mimesis2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_MimesisMutinyMar2022.jpg"/>
    <label text="bn_mimesisMutiny_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_mimesisMutiny_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=ab9a1f8407899527cb4dccad885809bb"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightRanking1aug2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1apr2021.jpg"/>
    <label text="bn_blacklightranking1aug2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1aug2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="AgatusBreach202503" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202503.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202503_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="newdawn202510" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_newdawn2024.jpg"/>
    <label text="bn_newdawn2024_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_newdawn2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=39c407e33c2093443d670ee04781b24f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="gear_progression_warning" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="warning_b_201910.jpg"/>
    <label text="bn_gearProgressionWarning_content" position="half_maintext" style="headline"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="agatusBreach202611" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202611.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202611_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking1Nov2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_1sep2022.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1nov2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="winterquests2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_winterquests2020.jpg"/>
    <label text="bn_winterQuests_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterQuests_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking1Mar2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_1sep2022.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1-mar2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking1may2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_bl_2024051.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1-may2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="frostDesignDec2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_FrostDesignSales_Dec2025.jpg"/>
    <label text="bn_WinterFrost2025_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_WinterFrost2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=bd451a600c545927173892d2fa2ac419"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mimesisMutiny" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="mimesis_mutiny_s_202002.jpg"/>
    <label text="bn_mimesisMutiny_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_mimesisMutiny_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blackfridaynov2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_BlackfridayNov2023.jpg"/>
    <label text="bn_blackfridaynov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blackfridaynov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4e4f4c346b09cdd763d3df24fe9c712b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange202512" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchant202512.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=f9cbd1162c4b54391dda68b84c3f5552"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="springDesign202604" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Spring202604.jpg"/>
    <label text="bn_springDesignMar2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_springDesignMar2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=e8bb0dd76cbd8b3851816a781e9697f8"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="test" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="bbox_apoc_s_201810.jpg"/>
    <label text="bn_apocReshuffle_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_apocReshuffle_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankingsAug2022_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralranking1aug2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=8f1e9c9686a00e1b63cbc98796cd0587"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="summerDesignJuly2025" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SummerDesign202507.jpg"/>
    <label text="bn_summerDesignJun2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_summerDesignJul2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=547d82cb94c6bdbb59003020adadb434"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_nov2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_Nov2023.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=ab965c5321e0703ba8799f311aa1d570"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="pvpBoost2019" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="sale_boost_up_seprom_pack_s_201904.jpg"/>
    <label text="bn_boost-up_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_boost-up_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d8769b51211ecd55890796ccad969b8d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendardec2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_miniclientcalendardec2021.jpg"/>
    <label text="bn_clientcalendardec2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendardec2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="tieredArena" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Tiered_Arena.jpg"/>
    <label text="bn_tieredArena_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_tieredArena_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=73d880edb86a3c08ef5a41fb21a9a148"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankings202412_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-dec2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankings202410_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-oct2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="uriBank_bonusAmmo" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="uriBank_bonusAmmo.jpg"/>
    <label text="bn_uridiumBank_bonus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_uriBank_bonusAmmo_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking1apr2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1apr2021.jpg"/>
    <label text="bn_blacklightranking1apr2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1apr2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="berserkerDesignAug" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_shipDesignAug2021.jpg"/>
    <label text="bn_berserkerDesignAug2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_berserkerDesignAug2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5c7ac75609b000fb747c0ec3691dca88"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="monthlyRankingUpdateJan2021" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_monthlyRankingUpdateJan2021.jpg"/>
    <label text="bn_monthlyRankingUpdateJan2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_monthlyRankingUpdateJan2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="AgatusBreach202409" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202409.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202409_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mimesis2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_mimesismutiny2023.jpg"/>
    <label text="bn_mimesisMutiny_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_Mimesis Mutiny_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=b17306ae88b19b2c228bfc6ca784f59b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202607" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202607.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202607_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="contentexpansion_202106_payment" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusoct2020.png"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankings202504_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-apr2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="tartarusDesigns2019" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="designdeal_tartarus_q3_s_201907.jpg"/>
    <label text="bn_tartarusDesigns2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_tartarusDesigns2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=9d667b357354d59fddebd01889b5ec54"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="frostDesignDec2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_frostDesignDec2020.jpg"/>
    <label text="bn_frostDesignDec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_frostDesignDec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=61e5431a838caf799debae4a3fdb896e"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsDec2024_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1jun2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-dec2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="spacecup202106" prio="4" countdown ="0" category = "events" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_spacecup202106.jpg"/>
    <label text="bn_spacecup202106_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_spacecup202106_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=656cb30856549894b177ee3fb0b168e7"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AAExpansion202210" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AstralAscensionExpansion.jpg"/>
    <label text="bn_AAExpansion202210_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_AAExpansion202210_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d0f2fbaea2e8d3cc493511fb0cbcb865"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendardec2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_clientcalendardec2020.png"/>
    <label text="bn_clientcalendardec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendardec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="worldBoss2026" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_worldboss_202506.jpg"/>
    <label text="bn_worldBoss202306_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_worldboss2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=fbaac43344577f3c012aa36b772b7b37"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking1jun2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1apr2021.jpg"/>
    <label text="bn_blacklightranking1jun2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1jun2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="InternalACPTest_TS_BN" prio="4" countdown ="1" category = "news" >
  <config>
    <event id="TsRSB-75HappyHour"/>
  </config>
  <assignments>
    <background assetID="ghh_ts_400_v04_b_201907.jpg"/>
    <label text="" position="half_headline" style="bold_full_content"/>
    <label text="be_blitz400tsChrominRSB_content" position="half_maintext" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="footer">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=04dc5c87431b5928f3d02905e1989408"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="gauntletOfPlutusJul2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_Gauntlet_of_Plutus_2022.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutusJul2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=32b8637c3a578be4a52ca6759daeae63"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking1nov2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1_Nov2023.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1nov2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking2may2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_bl_2024052.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2-may2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankingsJun2023_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-jun2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="carboniteDesigns2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_carboniteDesign.jpg"/>
    <label text="bn_carboniteDesigns2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_carboniteDesigns2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7de495d735632ab5b780a45d4f0d5e22"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="upgradeBonusHour" prio="4" countdown ="0" category = "news" >
  <config>
    <event id="HappyHourUpgradeSystem"/>
  </config>
  <assignments>
    <background assetID="upgrade_bonus_hour_s_201806.jpg"/>
    <label text="bn_upgradeBounsHour_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_upgradeBounsHour_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="orcusDesignMay_noGGdrop" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_orcusDesignMay2021.jpg"/>
    <label text="bn_orcusDesignMay2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_orcusDesignMay2021-noGGdrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=08129fb17e7fbc55d39a71efeac1e39f"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="clientcalendar202601" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_NewYearCalendar_2_202601.png"/>
    <label text="bn_newyearsales2025_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_clientcalendarjan2026-2_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="galacticStrife" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="DO_breakingnews_galacticStrifeMay2020.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=73d880edb86a3c08ef5a41fb21a9a148"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="AgatusBreach202412" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202412.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202412_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2sep2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking2_Nov2023.jpg"/>
    <label text="bn_blacklightranking1nov2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2nov2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blackFridayDiscount2019" prio="4" countdown ="1" category = "news" >
  <config>
    <event id="BE_blackFridayDiscount2019"/>
  </config>
  <assignments>
    <background assetID="deal_20percent_s_201911.jpg"/>
    <label text="bn_blackFridayDiscount2019_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blackFridayDiscount2019_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="agatusBreach202309" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_agatusBreach_202309.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202309_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="worldBoss202306" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_WorldBoss_Jun2023.jpg"/>
    <label text="bn_worldBoss202306_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_worldBoss202306_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=dd43e3d539330269dd8463ddc03b79eb"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="pveServer_starterSales" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_pveserverdec2020_paymentExclusive.jpg"/>
    <label text="bn_pveserverdec2020_paymentExclusive_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_pveserverdec2020_paymentExclusive_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <link href="?action=internalDock&#38;tpl=internalDockSpecials"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="astralrankingsDec2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1jun2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-dec2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=d0f2fbaea2e8d3cc493511fb0cbcb865"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="gauntletOfPlutus202601" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gauntletOfPlutusJan2026.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutusJan2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c3b347f475ec9f9b56e104ef7f6a40a5"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterquests2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_winterquests2020.jpg"/>
    <label text="bn_winterQuests2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterQuests_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking2Apr2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking2Apr2022.jpg"/>
    <label text="bn_blacklightranking2apr2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2apr2022_content2" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blackfridaynov2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_black_friday_nov2022_02.jpg"/>
    <label text="bn_blackfridaynov2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blackfridaynov2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=188a61f3be764adf9baf9292bb12fe15"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="VIPMerchantExchange202504" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_VIPMerchant202504.jpg"/>
    <label text="bn_VIP-Merchant-Exchange_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_VIP-Merchant-Exchange_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=5a929e4b33d68ca98db2b61d0f27d722"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202612" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202612.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202612_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="ggDrop_mimesisDesigns" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="designdeal_mimesis_q3_s_201908.jpg"/>
    <label text="bn_ggMimesisDrop_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_ggMimesisDrop_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking2Jul2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking2jul2023.jpg"/>
    <label text="bn_blacklightranking2apr2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2-jul2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="gauntletOfPlutus202607" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_gauntletOfPlutus202607_303x168.jpg"/>
    <label text="bn_gauntletOfPlutus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_gauntletOfPlutusJan2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=c3b347f475ec9f9b56e104ef7f6a40a5"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="monthlyDeluxePack20251030" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_monthlyDeluxePack102020.jpg"/>
    <label text="bn_monthlyDeluxePack102020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_monthlyDeluxePack20251030_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_category_deals"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=09ed46426cc29273586cdce107bcb681"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202610" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202610.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202610_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202603" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202603.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202603_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightRanking1sep2021" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightranking1apr2021.jpg"/>
    <label text="bn_blacklightranking1sep2021_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1sep2021_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankingsFeb2024_2" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking2.jpg"/>
    <label text="bn_astralranking2aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings2-feb2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=4ccec43545f2da6903a028e203dc5664"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="agatusBreach202608" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="AgatusBreach202608.jpg"/>
    <label text="bn_agatusBreach_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_agatusBreach-202608_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=11809eab0f7fbf52c7c987017e2d01bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_sep2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_GalacticStrife_Sep2023.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=ab965c5321e0703ba8799f311aa1d570"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unificationSaleOct2022" prio="4" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_UnificationSales_Oct2022.jpg"/>
    <label text="bn_unificationsaleoct2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unificationsaleoct2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=90c83d30e3160aec81246298755316b9"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="galacticStrife_apr2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_galacticStrife_202304.jpg"/>
    <label text="bn_galacticStrife_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_galacticStrife_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=727d10b82ad7593a3460f2bbe151be73"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="mimesis2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_mimesismutiny2024.jpg"/>
    <label text="bn_mimesisMutiny_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_Mimesis Mutiny_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=0bd9cf964906581822410d34bfe7d027"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="happynewyear2025" prio="4" countdown ="1" category = "news" >
  <config>
    <event id="BE_blackFridayDiscount2019"/>
  </config>
  <assignments>
    <background assetID="breaking_news_happynewyear_2025.png"/>
    <label text="bn_newyearsales2025_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_newyearsales2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="astralrankingsJun2025_1" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breakingnews_AstralRanking1.jpg"/>
    <label text="bn_astralranking1aug2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_astralrankings1-jun2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=cd7ebd5d9e51af05b5526da56bd090ec"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="blacklightranking2May2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_2sep2022.jpg"/>
    <label text="bn_blacklightranking2nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking2-may2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="autumnDesignSep2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_AutumnShipDesignSales_Sep2022.jpg"/>
    <label text="bn_autumnDesignSale2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_autumnDesignSale2022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=a7b78e086039dbcbbc93b533672842bd"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="winterdec2020" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_winterdec2020.jpg"/>
    <label text="bn_winterdec2020_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_winterdec2020_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=0cb2a63721d233b671ae5ec953dc7c33"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="frostDesignDec2024" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_FrostDesignSales_Dec2024.jpg"/>
    <label text="bn_WinterFrost2024_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_WinterFrost2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=7a099946770a3e74851142982e160463"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="pveServer_serverPromo" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_pveserverdec2020_otherServer.jpg"/>
    <label text="bn_pveserverdec2020_server_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_pveserverdec2020_server_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="pveServer_otherServerPromo" prio="4" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_pveserverdec2020_otherServer.jpg"/>
    <label text="bn_pveserverdec2020_otherServer_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_pveserverdec2020_otherServer_content" position="half_maintext_with_headline" style="footer_small"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking1Sep2022" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_1sep2022.jpg"/>
    <label text="bn_blacklightranking1sep2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1sep022_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="uriBank_bonusLogfiles" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="uriBank_bonusLogfiles.jpg"/>
    <label text="bn_uridiumBank_bonus_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_uriBank_bonusLogdisk_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="blacklightranking1Jan2023" prio="4" countdown ="1" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_blacklightRankings_1sep2022.jpg"/>
    <label text="bn_blacklightranking1nov2022_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_blacklightranking1-jan2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
  </actions>
</layer>

<layer name="salesrerun202407" prio="5" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_SalesRerun2022.jpg"/>
    <label text="bn_salesrerun_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_salesrerun_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=32f5d0cde81e26b0fc537c45e0cde616"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unificationSaleOct2023" prio="5" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_UnificationSales_Oct2023.jpg"/>
    <label text="bn_unificationsaleoct2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unificationsaleoct2023_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=af724599f73b00b0c3f4724e6e600cd5"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unificationSale202410" prio="5" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_UnificationSales_202410.jpg"/>
    <label text="bn_unificationsaleoct2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unificationsaleoct2024_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=370d4f60d9598e0c6f6fe4bd7291402c"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unificationsale202510" prio="5" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_UnificationSales_202510.jpg"/>
    <label text="bn_unificationsaleoct2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unificationsaleoct2025_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=1de6fbef3689a99b916e9bdfaaa56d5b"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="unificationsale202610" prio="5" countdown ="1" category = "deals" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_UnificationSales_Oct2026_303x168.jpg"/>
    <label text="bn_unificationsaleoct2023_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_unificationsaleoct2026_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_hh_button"  position="center">
      <onclick>
        <payment category="101" package="/?action=internalPaymentProxy&amp;req=&amp;v=70275215ef45c58f6a6c005efb8f783d"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="global3" prio="10" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="breaking_news_newdawn2024.jpg"/>
    <label text="global3_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_global3_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_faq_headline"  position="center">
      <onclick>
        <link href="https://board-en.darkorbit.com/threads/new-server-global-3-titan-ranking-event.129700/"/>
      </onclick>
    </button>
  </actions>
</layer>

<layer name="discord" prio="10" countdown ="0" category = "news" >
  <config>
  </config>
  <assignments>
    <background assetID="discord_s_201802.jpg"/>
    <label text="bn_discord_headline" position="half_headline" style="bold_full_content"/>
    <label text="bn_discord_content" position="half_maintext_with_headline" style="default"/>
  </assignments>
  <actions>
    <button style="defaultButton"  text="bn_discord_headline"  position="center">
      <onclick>
        <link href="https://discord.gg/j3MygA6"/>
      </onclick>
    </button>
  </actions>
</layer>
</root>