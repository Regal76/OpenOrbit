"""Eski ad: panel artık "OpenOrbit Panel.pyw" (bu dosya onu açar). Eski masaüstü kısayolları ve 2026-10-24'ten önce kurulan
panellerin güncelleyicisi (indirdiği arşivde bu dosyayı arar) için duruyor; silinirse o kurulumlar güncelleme alamaz.
Old name: the panel is now "OpenOrbit Panel.pyw" (this file opens it); kept for old shortcuts and older panels' updaters.
"""
import os
import runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'OpenOrbit Panel.pyw'), run_name='__main__')
