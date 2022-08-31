-- #1
-- select category.name, count(film_category.category_id) from category
--     join film_category on category.category_id = film_category.category_id
--     group by category.name;

-- #2
-- select actor.first_name, actor.last_name from actor join film_actor
--     on actor.actor_id = film_actor.actor_id join film
--     on film_actor.film_id = film.film_id group by actor.actor_id
--     order by sum(film.rental_duration) desc limit 10;

-- #3
-- select category.name, sum(film.rental_rate) as film_cost from category
--     join film_category on film_category.category_id = category.category_id
--     join film on film.film_id = film_category.film_id
--     group by category.category_id
--     order by film_cost desc limit 1;

-- #4
-- select film.title from film
--     join (select film_id from film
--             except
--             select film_id from inventory) as no_inv
--     on film.film_id = no_inv.film_id;

-- #5
-- with temp_table as
--     (select ar.first_name, ar.last_name, count(fm.film_id) as film_counter
--     from actor as ar
--     join film_actor fa on ar.actor_id = fa.actor_id
--     join film fm on fm.film_id = fa.film_id
--     join film_category fc on fc.film_id = fm.film_id
--     join category as cr on cr.category_id = fc.category_id
--     where cr.category_id = 3
--     group by ar.actor_id
--     order by film_counter desc)
-- select * from temp_table
--     where film_counter in (
--         select film_counter from temp_table
--             order by film_counter desc limit 3)
--     order by film_counter desc;

-- #6
-- select ct.city, count(case when active = 1 then 1 else 0 end) as active,
--        count(case when active = 0 then 1 else 0 end) as inactive from city as ct
--     join address as ad on ct.city_id = ad.city_id
--     join customer as cr on cr.address_id = ad.address_id
--     group by ct.city
--     order by inactive desc;

-- #7
-- select ct.city, sum(rl.return_date - rl.rental_date) as rent
--     from rental as rl
--     join customer as cr on rl.customer_id = cr.customer_id
--     join address as ad on ad.address_id = cr.address_id
--     join city as ct on ct.city_id = ad.city_id
--     where substring(ct.city, 1, 1) = 'a'
--     group by ct.city
--
-- union
--
-- select ct.city, sum(rl.return_date - rl.rental_date) as rent
--     from rental as rl
--     join customer as cr on rl.customer_id = cr.customer_id
--     join address as ad on ad.address_id = cr.address_id
--     join city as ct on ct.city_id = ad.city_id
--     where strpos(city, '-')!=0
--     group by ct.city;


