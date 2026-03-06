<?php
/**
 * Plugin Name: Content Factory — Шаблоны страниц
 * Description: Подменю «Страницы → Шаблоны страниц»: таблица шаблонов и редактирование блоками (Gutenberg).
 * Version: 1.0.0
 * Author: Content Factory
 * Text Domain: content-factory-page-templates
 * Domain Path: /languages
 */

defined( 'ABSPATH' ) || exit;

add_action( 'init', 'cfpt_register_page_templates_cpt' );

/**
 * Регистрирует тип записи «Шаблон страницы» и подменю в «Страницы».
 */
function cfpt_register_page_templates_cpt() {
	$labels = array(
		'name'               => 'Шаблоны страниц',
		'singular_name'      => 'Шаблон страницы',
		'menu_name'          => 'Шаблоны страниц',
		'add_new'            => 'Добавить шаблон',
		'add_new_item'       => 'Добавить новый шаблон',
		'edit_item'          => 'Редактировать шаблон',
		'new_item'            => 'Новый шаблон',
		'view_item'          => 'Просмотреть шаблон',
		'search_items'       => 'Искать шаблоны',
		'not_found'          => 'Шаблоны не найдены',
		'not_found_in_trash' => 'В корзине шаблонов нет',
		'all_items'          => 'Шаблоны страниц',
	);

	$args = array(
		'labels'              => $labels,
		'public'              => false,
		'publicly_queryable'  => false,
		'show_ui'             => true,
		'show_in_menu'        => 'edit.php?post_type=page',
		'show_in_rest'       => true,
		'rest_base'           => 'cf_page_templates',
		'capability_type'     => 'page',
		'map_meta_cap'        => true,
		'hierarchical'        => false,
		'menu_position'       => null,
		'supports'            => array( 'title', 'editor', 'revisions' ),
		'has_archive'        => false,
		'rewrite'             => false,
		'query_var'           => false,
	);

	register_post_type( 'cf_page_template', $args );
}

add_filter( 'manage_cf_page_template_posts_columns', 'cfpt_list_columns' );
add_action( 'manage_cf_page_template_posts_custom_column', 'cfpt_list_column_content', 10, 2 );

/**
 * Колонки таблицы списка шаблонов.
 *
 * @param array $columns Текущие колонки.
 * @return array
 */
function cfpt_list_columns( $columns ) {
	$new = array();
	foreach ( $columns as $key => $label ) {
		$new[ $key ] = $label;
		if ( $key === 'title' ) {
			$new['cfpt_date'] = 'Дата';
			$new['cfpt_author'] = 'Автор';
		}
	}
	return $new;
}

/**
 * Содержимое кастомных колонок.
 *
 * @param string $column  Имя колонки.
 * @param int    $post_id ID записи.
 */
function cfpt_list_column_content( $column, $post_id ) {
	$post = get_post( $post_id );
	if ( ! $post ) {
		return;
	}
	switch ( $column ) {
		case 'cfpt_date':
			echo esc_html( get_the_date( '', $post ) );
			break;
		case 'cfpt_author':
			echo esc_html( get_the_author_meta( 'display_name', $post->post_author ) );
			break;
	}
}
